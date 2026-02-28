"""Httpx-based scraper adapter implementing the ScraperPort protocol.

Fetches pages over HTTP/1.1 and HTTP/2 using an async httpx client with:
- Per-domain rate limiting enforced via asyncio.sleep
- Optional robots.txt compliance with in-memory caching
- Bounded concurrency via asyncio.Semaphore
- Content-type detection from response headers
- Idempotent resource cleanup

This adapter is suitable for static pages that do not require JavaScript
rendering. For SPAs or dynamic content, use the Playwright adapter instead.
"""

from __future__ import annotations

import asyncio
import logging
import urllib.robotparser
import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING
from urllib.parse import urlparse

import httpx

from searchmuse.domain.enums import ContentType
from searchmuse.domain.errors import RequestTimeoutError, RobotsTxtBlockedError, ScrapingError
from searchmuse.domain.models import ScrapedPage

if TYPE_CHECKING:
    from searchmuse.infrastructure.config import ScrapingConfig

logger: logging.Logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Internal constants
# ---------------------------------------------------------------------------

_SCRAPER_ID: str = "httpx"

_CONTENT_TYPE_MAP: tuple[tuple[str, ContentType], ...] = (
    ("text/html", ContentType.HTML),
    ("application/xhtml+xml", ContentType.HTML),
    ("application/pdf", ContentType.PDF),
    ("application/json", ContentType.JSON),
    ("text/plain", ContentType.PLAIN_TEXT),
)

_ROBOTS_TXT_TIMEOUT: float = 5.0
_ROBOTS_TXT_PATH: str = "/robots.txt"


# ---------------------------------------------------------------------------
# Adapter
# ---------------------------------------------------------------------------


class HttpxScraperAdapter:
    """Scraper adapter backed by an async httpx client.

    Satisfies the ScraperPort protocol for static HTTP(S) pages. The
    underlying AsyncClient is created lazily on the first request so that
    construction is always synchronous and cheap.

    Args:
        config: Frozen scraping configuration loaded from the application
            config file or environment.
    """

    def __init__(self, config: ScrapingConfig) -> None:
        self._config: ScrapingConfig = config
        self._client: httpx.AsyncClient | None = None

        # Per-domain rate-limiting: maps domain -> last request timestamp
        self._last_request_times: dict[str, float] = {}

        # Robots.txt cache: maps domain -> RobotFileParser (already fetched)
        self._robots_cache: dict[str, urllib.robotparser.RobotFileParser] = {}

    # ------------------------------------------------------------------
    # Public protocol methods
    # ------------------------------------------------------------------

    async def scrape(self, url: str) -> ScrapedPage:
        """Fetch a single URL and return the raw page.

        Applies rate limiting and robots.txt checks before issuing the
        HTTP request. The page_id is generated as a fresh UUID4.

        Args:
            url: A validated http(s) URL to fetch.

        Returns:
            A frozen ScrapedPage with the raw HTML body and metadata.

        Raises:
            RobotsTxtBlockedError: When robots.txt disallows the URL and
                ``respect_robots_txt`` is enabled in config.
            RequestTimeoutError: When the request exceeds
                ``request_timeout`` seconds.
            ScrapingError: For any other httpx transport error.
        """
        client = self._get_client()
        domain = _extract_domain(url)

        await self._enforce_rate_limit(domain)

        if self._config.respect_robots_txt:
            await self._check_robots_txt(url, domain, client)

        return await self._fetch(url, client)

    async def scrape_many(self, urls: tuple[str, ...]) -> tuple[ScrapedPage, ...]:
        """Fetch multiple URLs concurrently with bounded parallelism.

        Concurrency is capped at ``max_concurrent`` requests in flight at
        once. Individual failures are logged and silently dropped so the
        caller always receives only successfully scraped pages.

        Args:
            urls: A tuple of validated http(s) URLs to fetch.

        Returns:
            A tuple of ScrapedPage instances for every URL that succeeded.
        """
        semaphore = asyncio.Semaphore(self._config.max_concurrent)

        async def _bounded_scrape(url: str) -> ScrapedPage | None:
            async with semaphore:
                try:
                    return await self.scrape(url)
                except ScrapingError as exc:
                    logger.warning("Scrape failed, skipping URL %r: %s", url, exc)
                    return None
                except Exception as exc:
                    logger.error(
                        "Unexpected error while scraping %r: %s",
                        url,
                        exc,
                        exc_info=True,
                    )
                    return None

        results = await asyncio.gather(*(_bounded_scrape(url) for url in urls))
        return tuple(page for page in results if page is not None)

    def can_handle(self, url: str) -> bool:
        """Return True for any http or https URL.

        Args:
            url: The URL to check.

        Returns:
            True when the scheme is ``http`` or ``https``.
        """
        scheme = urlparse(url).scheme.lower()
        return scheme in {"http", "https"}

    async def close(self) -> None:
        """Close the underlying httpx client if it has been initialised.

        This method is idempotent; calling it on an already-closed or
        never-opened adapter is a no-op.
        """
        if self._client is not None:
            await self._client.aclose()
            self._client = None
            logger.debug("HttpxScraperAdapter: client closed")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_client(self) -> httpx.AsyncClient:
        """Return the shared AsyncClient, creating it lazily on first call.

        The client is configured with HTTP/2 support, the configured user
        agent, and the request timeout from ScrapingConfig.

        Returns:
            The lazily-initialised shared AsyncClient instance.
        """
        if self._client is None:
            self._client = httpx.AsyncClient(
                http2=True,
                headers={"User-Agent": self._config.user_agent},
                timeout=httpx.Timeout(float(self._config.request_timeout)),
                follow_redirects=True,
            )
            logger.debug(
                "HttpxScraperAdapter: client initialised (timeout=%ds, http2=True)",
                self._config.request_timeout,
            )
        return self._client

    async def _enforce_rate_limit(self, domain: str) -> None:
        """Sleep if needed to respect the configured per-domain request delay.

        Reads the last request timestamp for ``domain`` and sleeps for the
        remaining fraction of ``request_delay`` if not enough time has
        elapsed since the previous request.

        Args:
            domain: The normalised hostname (e.g. ``"example.com"``).
        """
        last_time = self._last_request_times.get(domain)
        if last_time is not None:
            elapsed = asyncio.get_running_loop().time() - last_time
            wait = self._config.request_delay - elapsed
            if wait > 0:
                logger.debug(
                    "Rate limiting: sleeping %.2fs before request to %r", wait, domain
                )
                await asyncio.sleep(wait)
        self._last_request_times = {**self._last_request_times, domain: asyncio.get_running_loop().time()}

    async def _check_robots_txt(
        self, url: str, domain: str, client: httpx.AsyncClient
    ) -> None:
        """Verify that robots.txt permits access to ``url``.

        Fetches and caches the robots.txt document for ``domain`` on the
        first call, then uses the cached parser for subsequent checks.
        Network errors while fetching robots.txt are logged and treated as
        permissive (access is allowed).

        Args:
            url: The target URL being checked.
            domain: The hostname of the target URL.
            client: The shared AsyncClient used for the robots.txt request.

        Raises:
            RobotsTxtBlockedError: When the parser signals that the
                configured user agent is disallowed from ``url``.
        """
        parser = await self._get_robots_parser(domain, client)
        if not parser.can_fetch(self._config.user_agent, url):
            logger.info("robots.txt blocks %r for agent %r", url, self._config.user_agent)
            raise RobotsTxtBlockedError(
                f"Disallowed by robots.txt on {domain!r}",
                url=url,
            )

    async def _get_robots_parser(
        self, domain: str, client: httpx.AsyncClient
    ) -> urllib.robotparser.RobotFileParser:
        """Return a cached RobotFileParser for ``domain``, fetching if needed.

        Args:
            domain: The hostname whose robots.txt is requested.
            client: The AsyncClient used for the HTTP GET.

        Returns:
            A populated RobotFileParser. If the fetch fails the parser is
            returned in a permissive default state (all paths allowed).
        """
        if domain in self._robots_cache:
            return self._robots_cache[domain]

        robots_url = f"https://{domain}{_ROBOTS_TXT_PATH}"
        parser = urllib.robotparser.RobotFileParser(url=robots_url)

        try:
            response = await client.get(
                robots_url,
                timeout=httpx.Timeout(_ROBOTS_TXT_TIMEOUT),
            )
            parser.parse(response.text.splitlines())
            logger.debug("Fetched robots.txt for %r (status %d)", domain, response.status_code)
        except Exception as exc:
            logger.warning(
                "Could not fetch robots.txt for %r: %s — treating as permissive",
                domain,
                exc,
            )

        self._robots_cache = {**self._robots_cache, domain: parser}
        return parser

    async def _fetch(self, url: str, client: httpx.AsyncClient) -> ScrapedPage:
        """Issue the HTTP GET and build a ScrapedPage from the response.

        Enforces the ``max_page_size`` limit by reading only up to that
        many bytes from the response body.

        Args:
            url: The URL to fetch.
            client: The shared AsyncClient.

        Returns:
            A frozen ScrapedPage populated from the HTTP response.

        Raises:
            RequestTimeoutError: When the request exceeds the timeout.
            ScrapingError: For any other httpx transport failure.
        """
        try:
            response = await client.get(url)
            raw_body = response.text[: self._config.max_page_size]
            content_type = _detect_content_type(response.headers.get("content-type", ""))

            page = ScrapedPage(
                page_id=str(uuid.uuid4()),
                url=url,
                raw_html=raw_body,
                http_status=response.status_code,
                content_type=content_type,
                scraped_at=datetime.now(UTC),
                scraper_used=_SCRAPER_ID,
            )
            logger.debug(
                "Scraped %r -> HTTP %d, content_type=%s, body_len=%d",
                url,
                response.status_code,
                content_type,
                len(raw_body),
            )
            return page

        except httpx.TimeoutException as exc:
            raise RequestTimeoutError(
                f"Request timed out after {self._config.request_timeout}s",
                url=url,
            ) from exc
        except httpx.HTTPError as exc:
            raise ScrapingError(
                f"HTTP error while fetching {url!r}: {exc}",
                url=url,
            ) from exc


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------


def _extract_domain(url: str) -> str:
    """Return the lowercase hostname from a URL string.

    Args:
        url: A fully-qualified URL such as ``"https://example.com/path"``.

    Returns:
        The hostname portion, e.g. ``"example.com"``.
    """
    return urlparse(url).hostname or url


def _detect_content_type(content_type_header: str) -> ContentType:
    """Map an HTTP Content-Type header value to a domain ContentType enum.

    The function matches on the leading MIME type token, ignoring charset
    parameters and other directives. Falls back to ``ContentType.HTML``
    when the header is absent or unrecognised.

    Args:
        content_type_header: The raw value of the ``Content-Type`` header,
            e.g. ``"text/html; charset=utf-8"``.

    Returns:
        The closest matching :class:`ContentType` member.
    """
    # Strip parameters (e.g. "; charset=utf-8") and normalise case
    mime = content_type_header.split(";", maxsplit=1)[0].strip().lower()

    for prefix, content_type in _CONTENT_TYPE_MAP:
        if mime == prefix or mime.startswith(prefix):
            return content_type

    return ContentType.HTML
