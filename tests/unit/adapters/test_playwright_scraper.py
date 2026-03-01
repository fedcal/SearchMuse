"""Tests for searchmuse.adapters.scrapers.playwright_scraper."""

from unittest.mock import AsyncMock

import pytest

from searchmuse.adapters.scrapers.playwright_scraper import PlaywrightScraperAdapter
from searchmuse.infrastructure.config import ScrapingConfig


@pytest.fixture()
def scraping_config():
    return ScrapingConfig(
        request_delay=0.0,
        request_timeout=10,
        max_concurrent=2,
        respect_robots_txt=False,
        user_agent="Test/1.0",
        use_playwright=True,
        max_page_size=1_000_000,
    )


def test_can_handle_http(scraping_config):
    adapter = PlaywrightScraperAdapter(config=scraping_config)
    assert adapter.can_handle("http://example.com") is True
    assert adapter.can_handle("https://example.com") is True


def test_can_handle_ftp(scraping_config):
    adapter = PlaywrightScraperAdapter(config=scraping_config)
    assert adapter.can_handle("ftp://example.com") is False


@pytest.mark.asyncio
async def test_close_noop_when_no_browser(scraping_config):
    adapter = PlaywrightScraperAdapter(config=scraping_config)
    await adapter.close()  # Should not raise


@pytest.mark.asyncio
async def test_scrape_creates_scraped_page(scraping_config):
    adapter = PlaywrightScraperAdapter(config=scraping_config)

    mock_page = AsyncMock()
    mock_page.content.return_value = "<html><body>Hello</body></html>"
    mock_page.close = AsyncMock()

    mock_browser = AsyncMock()
    mock_browser.new_page.return_value = mock_page

    adapter._browser = mock_browser

    page = await adapter.scrape("https://example.com")
    assert page.url == "https://example.com"
    assert page.scraper_used == "playwright"
    assert "<html>" in page.raw_html
    mock_page.goto.assert_called_once()


@pytest.mark.asyncio
async def test_scrape_many_handles_failures(scraping_config):
    adapter = PlaywrightScraperAdapter(config=scraping_config)

    call_count = 0

    async def mock_scrape(url):
        nonlocal call_count
        call_count += 1
        if "fail" in url:
            from searchmuse.domain.errors import ScrapingError
            raise ScrapingError("failed", url=url)
        from datetime import UTC, datetime
        from uuid import uuid4

        from searchmuse.domain.enums import ContentType
        from searchmuse.domain.models import ScrapedPage
        return ScrapedPage(
            page_id=str(uuid4()),
            url=url,
            raw_html="<html></html>",
            http_status=200,
            content_type=ContentType.HTML,
            scraped_at=datetime.now(UTC),
            scraper_used="playwright",
        )

    adapter.scrape = mock_scrape  # type: ignore[assignment]
    results = await adapter.scrape_many(("https://ok.com", "https://fail.com"))
    assert len(results) == 1
    assert results[0].url == "https://ok.com"
