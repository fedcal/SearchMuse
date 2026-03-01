"""Playwright-based scraper adapter implementing the ScraperPort protocol.

Uses a headless Chromium browser for JavaScript-rendered pages.
Features:
- Lazy browser launch on first request
- Per-domain rate limiting via asyncio.sleep
- Bounded concurrency via asyncio.Semaphore
- Page size limiting
- Idempotent cleanup
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING
from urllib.parse import urlparse

from searchmuse.domain.enums import ContentType
from searchmuse.domain.errors import RequestTimeoutError, ScrapingError
from searchmuse.domain.models import ScrapedPage

if TYPE_CHECKING:
    from playwright.async_api import Browser

    from searchmuse.infrastructure.config import ScrapingConfig

logger: logging.Logger = logging.getLogger(__name__)

_SCRAPER_ID: str = "playwright"


class PlaywrightScraperAdapter:
    """Scraper adapter backed by Playwright Chromium for JS-rendered pages.

    Satisfies the ScraperPort protocol. The browser is launched lazily on
    the first request so construction is always synchronous.

    Args:
        config: Frozen scraping configuration from the application config.
    """

    def __init__(self, config: ScrapingConfig) -> None:
        self._config: ScrapingConfig = config
        self._browser: Browser | None = None
        self._last_request_times: dict[str, float] = {}

    async def _get_browser(self) -> Browser:
        """Return the shared Browser instance, launching it lazily."""
        if self._browser is None:
            from playwright.async_api import async_playwright

            pw = await async_playwright().start()
            self._browser = await pw.chromium.launch(headless=True)
            logger.debug("Playwright: Chromium browser launched (headless)")
        return self._browser

    async def scrape(self, url: str) -> ScrapedPage:
        """Fetch a single URL with a headless browser and return the raw page.

        Navigates to the URL with ``wait_until="networkidle"`` to ensure
        JavaScript-rendered content is fully loaded.

        Args:
            url: A validated http(s) URL to fetch.

        Returns:
            A frozen ScrapedPage with the rendered HTML.

        Raises:
            RequestTimeoutError: When the page load exceeds timeout.
            ScrapingError: For any other Playwright error.
        """
        browser = await self._get_browser()
        domain = _extract_domain(url)
        await self._enforce_rate_limit(domain)

        page = await browser.new_page(
            user_agent=self._config.user_agent,
        )

        try:
            timeout_ms = self._config.request_timeout * 1000
            await page.goto(url, wait_until="networkidle", timeout=timeout_ms)

            html = await page.content()
            truncated_html = html[: self._config.max_page_size]

            scraped = ScrapedPage(
                page_id=str(uuid.uuid4()),
                url=url,
                raw_html=truncated_html,
                http_status=200,
                content_type=ContentType.HTML,
                scraped_at=datetime.now(UTC),
                scraper_used=_SCRAPER_ID,
            )
            logger.debug(
                "Playwright scraped %r, body_len=%d", url, len(truncated_html)
            )
            return scraped

        except Exception as exc:
            exc_name = type(exc).__name__
            if "timeout" in exc_name.lower() or "Timeout" in str(exc):
                raise RequestTimeoutError(
                    f"Page load timed out after {self._config.request_timeout}s",
                    url=url,
                ) from exc
            raise ScrapingError(
                f"Playwright error while fetching {url!r}: {exc}",
                url=url,
            ) from exc
        finally:
            await page.close()

    async def scrape_many(self, urls: tuple[str, ...]) -> tuple[ScrapedPage, ...]:
        """Fetch multiple URLs concurrently with bounded parallelism.

        Args:
            urls: A tuple of validated http(s) URLs.

        Returns:
            A tuple of successfully scraped pages.
        """
        semaphore = asyncio.Semaphore(self._config.max_concurrent)

        async def _bounded_scrape(url: str) -> ScrapedPage | None:
            async with semaphore:
                try:
                    return await self.scrape(url)
                except ScrapingError as exc:
                    logger.warning("Playwright scrape failed for %r: %s", url, exc)
                    return None
                except Exception as exc:
                    logger.error(
                        "Unexpected error scraping %r: %s", url, exc, exc_info=True
                    )
                    return None

        results = await asyncio.gather(*(_bounded_scrape(u) for u in urls))
        return tuple(page for page in results if page is not None)

    def can_handle(self, url: str) -> bool:
        """Return True for any http or https URL.

        Args:
            url: The URL to check.

        Returns:
            True when the scheme is http or https.
        """
        scheme = urlparse(url).scheme.lower()
        return scheme in {"http", "https"}

    async def close(self) -> None:
        """Close the underlying browser if it has been launched.

        Idempotent: calling close on an already-closed adapter is a no-op.
        """
        if self._browser is not None:
            await self._browser.close()
            self._browser = None
            logger.debug("Playwright: browser closed")

    async def _enforce_rate_limit(self, domain: str) -> None:
        """Sleep if needed to respect per-domain request delay."""
        last_time = self._last_request_times.get(domain)
        if last_time is not None:
            elapsed = asyncio.get_running_loop().time() - last_time
            wait = self._config.request_delay - elapsed
            if wait > 0:
                logger.debug(
                    "Playwright rate limit: sleeping %.2fs for %r", wait, domain
                )
                await asyncio.sleep(wait)
        self._last_request_times = {
            **self._last_request_times,
            domain: asyncio.get_running_loop().time(),
        }


def _extract_domain(url: str) -> str:
    """Return the lowercase hostname from a URL."""
    return urlparse(url).hostname or url
