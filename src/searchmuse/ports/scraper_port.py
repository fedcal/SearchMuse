"""Protocol definition for web scraper adapter port."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from searchmuse.domain.models import ScrapedPage


@runtime_checkable
class ScraperPort(Protocol):
    """Abstract port for fetching raw page content from URLs.

    Implementations handle HTTP requests, optional JavaScript rendering,
    rate limiting, and robots.txt compliance.
    All async methods raise ScrapingError subclasses on failure.
    """

    async def scrape(self, url: str) -> ScrapedPage:
        """Fetch a single URL and return the raw page.

        Args:
            url: A validated http(s) URL to fetch.

        Returns:
            A frozen ScrapedPage with the raw HTML and metadata.
        """
        ...

    async def scrape_many(self, urls: tuple[str, ...]) -> tuple[ScrapedPage, ...]:
        """Fetch multiple URLs concurrently.

        Implementations should respect max_concurrent configuration.
        Partial failures are swallowed per-URL; the caller receives
        only successfully scraped pages.

        Args:
            urls: A tuple of validated http(s) URLs to fetch.

        Returns:
            A tuple of ScrapedPage instances for successful fetches.
        """
        ...

    def can_handle(self, url: str) -> bool:
        """Return True if this scraper can handle the given URL.

        Used by a composite scraper to select the appropriate adapter
        (e.g. Playwright for SPAs, httpx for static pages).

        Args:
            url: The URL to check.

        Returns:
            True when this scraper is able to process the URL.
        """
        ...

    async def close(self) -> None:
        """Release any held resources (sessions, browser instances).

        Must be idempotent; calling close() on an already-closed
        scraper must not raise.
        """
        ...
