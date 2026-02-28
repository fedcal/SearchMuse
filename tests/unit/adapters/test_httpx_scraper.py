"""Unit tests for HttpxScraperAdapter.

HTTP responses are mocked with respx so no real network calls are made.
All async tests run automatically via asyncio_mode = "auto" (pytest-asyncio).
"""

from __future__ import annotations

from unittest.mock import patch

import httpx
import pytest
import respx

from searchmuse.adapters.scrapers.httpx_scraper import HttpxScraperAdapter
from searchmuse.domain.enums import ContentType
from searchmuse.domain.errors import RequestTimeoutError, RobotsTxtBlockedError, ScrapingError
from searchmuse.domain.models import ScrapedPage
from searchmuse.infrastructure.config import ScrapingConfig

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

BASE_CONFIG = ScrapingConfig(
    request_delay=0.0,
    request_timeout=30,
    max_concurrent=5,
    respect_robots_txt=False,
    user_agent="Test/1.0",
    use_playwright=False,
    max_page_size=5242880,
)

ROBOTS_CONFIG = ScrapingConfig(
    request_delay=0.0,
    request_timeout=30,
    max_concurrent=5,
    respect_robots_txt=True,
    user_agent="Test/1.0",
    use_playwright=False,
    max_page_size=5242880,
)

RATE_LIMIT_CONFIG = ScrapingConfig(
    request_delay=1.0,
    request_timeout=30,
    max_concurrent=5,
    respect_robots_txt=False,
    user_agent="Test/1.0",
    use_playwright=False,
    max_page_size=5242880,
)


@pytest.fixture()
def adapter() -> HttpxScraperAdapter:
    """Adapter with robots.txt disabled and zero request delay."""
    return HttpxScraperAdapter(config=BASE_CONFIG)


@pytest.fixture()
def robots_adapter() -> HttpxScraperAdapter:
    """Adapter with robots.txt enforcement enabled."""
    return HttpxScraperAdapter(config=ROBOTS_CONFIG)


@pytest.fixture()
def rate_limit_adapter() -> HttpxScraperAdapter:
    """Adapter configured with a 1-second per-domain request delay."""
    return HttpxScraperAdapter(config=RATE_LIMIT_CONFIG)


# ---------------------------------------------------------------------------
# can_handle
# ---------------------------------------------------------------------------


class TestCanHandle:
    """can_handle must accept http/https and reject all other schemes."""

    def test_accepts_http(self, adapter: HttpxScraperAdapter) -> None:
        assert adapter.can_handle("http://example.com/page") is True

    def test_accepts_https(self, adapter: HttpxScraperAdapter) -> None:
        assert adapter.can_handle("https://example.com/page") is True

    def test_rejects_ftp(self, adapter: HttpxScraperAdapter) -> None:
        assert adapter.can_handle("ftp://files.example.com/file.txt") is False

    def test_rejects_file_scheme(self, adapter: HttpxScraperAdapter) -> None:
        assert adapter.can_handle("file:///home/user/doc.html") is False

    def test_rejects_no_scheme(self, adapter: HttpxScraperAdapter) -> None:
        assert adapter.can_handle("example.com/page") is False

    def test_accepts_https_mixed_case_scheme(self, adapter: HttpxScraperAdapter) -> None:
        # urlparse lowercases the scheme, so HTTPS: should still be recognised.
        assert adapter.can_handle("HTTPS://example.com/page") is True


# ---------------------------------------------------------------------------
# scrape — happy path
# ---------------------------------------------------------------------------


class TestScrapeSuccess:
    """scrape must return a well-formed ScrapedPage on a successful 200 response."""

    @respx.mock
    async def test_returns_scraped_page_instance(self, adapter: HttpxScraperAdapter) -> None:
        respx.get("https://example.com/page").mock(
            return_value=httpx.Response(200, text="<html>Hello</html>")
        )

        page = await adapter.scrape("https://example.com/page")

        assert isinstance(page, ScrapedPage)

    @respx.mock
    async def test_page_url_matches_request(self, adapter: HttpxScraperAdapter) -> None:
        target = "https://example.com/article"
        respx.get(target).mock(return_value=httpx.Response(200, text="<html></html>"))

        page = await adapter.scrape(target)

        assert page.url == target

    @respx.mock
    async def test_page_raw_html_captured(self, adapter: HttpxScraperAdapter) -> None:
        body = "<html><body>Content</body></html>"
        respx.get("https://example.com/").mock(return_value=httpx.Response(200, text=body))

        page = await adapter.scrape("https://example.com/")

        assert page.raw_html == body

    @respx.mock
    async def test_page_http_status_captured(self, adapter: HttpxScraperAdapter) -> None:
        respx.get("https://example.com/").mock(return_value=httpx.Response(200, text="ok"))

        page = await adapter.scrape("https://example.com/")

        assert page.http_status == 200

    @respx.mock
    async def test_content_type_html_detected(self, adapter: HttpxScraperAdapter) -> None:
        respx.get("https://example.com/").mock(
            return_value=httpx.Response(
                200, text="<html></html>", headers={"content-type": "text/html; charset=utf-8"}
            )
        )

        page = await adapter.scrape("https://example.com/")

        assert page.content_type == ContentType.HTML

    @respx.mock
    async def test_content_type_json_detected(self, adapter: HttpxScraperAdapter) -> None:
        respx.get("https://example.com/api").mock(
            return_value=httpx.Response(
                200, text='{"key": "val"}', headers={"content-type": "application/json"}
            )
        )

        page = await adapter.scrape("https://example.com/api")

        assert page.content_type == ContentType.JSON

    @respx.mock
    async def test_scraper_used_is_httpx(self, adapter: HttpxScraperAdapter) -> None:
        respx.get("https://example.com/").mock(return_value=httpx.Response(200, text="ok"))

        page = await adapter.scrape("https://example.com/")

        assert page.scraper_used == "httpx"

    @respx.mock
    async def test_page_id_is_unique_across_calls(self, adapter: HttpxScraperAdapter) -> None:
        respx.get("https://example.com/").mock(return_value=httpx.Response(200, text="ok"))

        page_a = await adapter.scrape("https://example.com/")
        page_b = await adapter.scrape("https://example.com/")

        assert page_a.page_id != page_b.page_id


# ---------------------------------------------------------------------------
# scrape — error cases
# ---------------------------------------------------------------------------


class TestScrapeErrors:
    """scrape must translate httpx errors into domain error types."""

    @respx.mock
    async def test_timeout_raises_request_timeout_error(
        self, adapter: HttpxScraperAdapter
    ) -> None:
        respx.get("https://example.com/slow").mock(side_effect=httpx.TimeoutException("timed out"))

        with pytest.raises(RequestTimeoutError) as exc_info:
            await adapter.scrape("https://example.com/slow")

        assert exc_info.value.url == "https://example.com/slow"

    @respx.mock
    async def test_http_error_raises_scraping_error(self, adapter: HttpxScraperAdapter) -> None:
        respx.get("https://example.com/bad").mock(
            side_effect=httpx.ConnectError("connection refused")
        )

        with pytest.raises(ScrapingError) as exc_info:
            await adapter.scrape("https://example.com/bad")

        assert exc_info.value.url == "https://example.com/bad"

    @respx.mock
    async def test_timeout_error_is_subclass_of_scraping_error(
        self, adapter: HttpxScraperAdapter
    ) -> None:
        respx.get("https://example.com/slow").mock(side_effect=httpx.TimeoutException("timeout"))

        with pytest.raises(ScrapingError):
            await adapter.scrape("https://example.com/slow")


# ---------------------------------------------------------------------------
# scrape_many
# ---------------------------------------------------------------------------


class TestScrapeMany:
    """scrape_many must return successful pages and silently drop failed ones."""

    @respx.mock
    async def test_returns_all_successful_pages(self, adapter: HttpxScraperAdapter) -> None:
        respx.get("https://alpha.com/").mock(return_value=httpx.Response(200, text="alpha"))
        respx.get("https://beta.com/").mock(return_value=httpx.Response(200, text="beta"))

        pages = await adapter.scrape_many(("https://alpha.com/", "https://beta.com/"))

        assert len(pages) == 2

    @respx.mock
    async def test_skips_failed_urls(self, adapter: HttpxScraperAdapter) -> None:
        respx.get("https://good.com/").mock(return_value=httpx.Response(200, text="good"))
        respx.get("https://bad.com/").mock(side_effect=httpx.ConnectError("refused"))

        pages = await adapter.scrape_many(("https://good.com/", "https://bad.com/"))

        assert len(pages) == 1
        assert pages[0].url == "https://good.com/"

    @respx.mock
    async def test_all_fail_returns_empty_tuple(self, adapter: HttpxScraperAdapter) -> None:
        respx.get("https://fail1.com/").mock(side_effect=httpx.ConnectError("refused"))
        respx.get("https://fail2.com/").mock(side_effect=httpx.TimeoutException("timeout"))

        pages = await adapter.scrape_many(("https://fail1.com/", "https://fail2.com/"))

        assert pages == ()

    @respx.mock
    async def test_returns_tuple_type(self, adapter: HttpxScraperAdapter) -> None:
        respx.get("https://example.com/").mock(return_value=httpx.Response(200, text="ok"))

        result = await adapter.scrape_many(("https://example.com/",))

        assert isinstance(result, tuple)

    @respx.mock
    async def test_empty_input_returns_empty_tuple(self, adapter: HttpxScraperAdapter) -> None:
        pages = await adapter.scrape_many(())

        assert pages == ()


# ---------------------------------------------------------------------------
# robots.txt
# ---------------------------------------------------------------------------


class TestRobotsTxt:
    """When respect_robots_txt=True, blocked URLs must raise RobotsTxtBlockedError."""

    @respx.mock
    async def test_raises_when_disallowed(self, robots_adapter: HttpxScraperAdapter) -> None:
        robots_body = "User-agent: *\nDisallow: /private/\n"
        respx.get("https://example.com/robots.txt").mock(
            return_value=httpx.Response(200, text=robots_body)
        )

        with pytest.raises(RobotsTxtBlockedError) as exc_info:
            await robots_adapter.scrape("https://example.com/private/data")

        assert exc_info.value.url == "https://example.com/private/data"

    @respx.mock
    async def test_allows_when_permitted(self, robots_adapter: HttpxScraperAdapter) -> None:
        robots_body = "User-agent: *\nDisallow: /private/\n"
        respx.get("https://example.com/robots.txt").mock(
            return_value=httpx.Response(200, text=robots_body)
        )
        respx.get("https://example.com/public/page").mock(
            return_value=httpx.Response(200, text="<html>ok</html>")
        )

        page = await robots_adapter.scrape("https://example.com/public/page")

        assert page.url == "https://example.com/public/page"

    @respx.mock
    async def test_blocks_when_robots_fetch_fails_and_parser_uninitialised(
        self, robots_adapter: HttpxScraperAdapter
    ) -> None:
        """When the robots.txt fetch fails, urllib.robotparser returns can_fetch=False
        in its default uninitialised state, so RobotsTxtBlockedError is raised.

        Note: the source log says "treating as permissive" but that refers to the
        exception being swallowed; the parser object itself has no rules loaded and
        its default can_fetch() returns False for all paths.
        """
        respx.get("https://flaky.com/robots.txt").mock(
            side_effect=httpx.ConnectError("refused")
        )
        # The page route is never reached because the robots check blocks first.

        with pytest.raises(RobotsTxtBlockedError):
            await robots_adapter.scrape("https://flaky.com/page")

    @respx.mock
    async def test_robots_txt_is_cached_per_domain(
        self, robots_adapter: HttpxScraperAdapter
    ) -> None:
        """The robots.txt file for a domain should only be fetched once."""
        robots_body = "User-agent: *\nAllow: /\n"
        robots_route = respx.get("https://cached.com/robots.txt").mock(
            return_value=httpx.Response(200, text=robots_body)
        )
        respx.get("https://cached.com/page1").mock(
            return_value=httpx.Response(200, text="page1")
        )
        respx.get("https://cached.com/page2").mock(
            return_value=httpx.Response(200, text="page2")
        )

        await robots_adapter.scrape("https://cached.com/page1")
        await robots_adapter.scrape("https://cached.com/page2")

        assert robots_route.call_count == 1


# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------


class TestRateLimiting:
    """_enforce_rate_limit must call asyncio.sleep when delay has not elapsed."""

    @respx.mock
    async def test_sleep_called_between_requests_to_same_domain(
        self, rate_limit_adapter: HttpxScraperAdapter
    ) -> None:
        respx.get("https://slow.com/page1").mock(
            return_value=httpx.Response(200, text="page1")
        )
        respx.get("https://slow.com/page2").mock(
            return_value=httpx.Response(200, text="page2")
        )

        with patch("searchmuse.adapters.scrapers.httpx_scraper.asyncio.sleep") as mock_sleep:
            mock_sleep.return_value = None
            # First request: no prior timestamp, sleep not called.
            await rate_limit_adapter.scrape("https://slow.com/page1")
            first_call_count = mock_sleep.call_count

            # Second request to same domain: rate limit should trigger.
            await rate_limit_adapter.scrape("https://slow.com/page2")
            second_call_count = mock_sleep.call_count

        # sleep must have been called at least once more after the second request.
        assert second_call_count > first_call_count

    @respx.mock
    async def test_no_sleep_on_first_request_to_domain(
        self, rate_limit_adapter: HttpxScraperAdapter
    ) -> None:
        respx.get("https://fresh.com/page").mock(
            return_value=httpx.Response(200, text="ok")
        )

        with patch("searchmuse.adapters.scrapers.httpx_scraper.asyncio.sleep") as mock_sleep:
            mock_sleep.return_value = None
            await rate_limit_adapter.scrape("https://fresh.com/page")

        mock_sleep.assert_not_called()

    @respx.mock
    async def test_no_sleep_when_delay_is_zero(self, adapter: HttpxScraperAdapter) -> None:
        """With request_delay=0.0 sleep must never be called even on repeated requests."""
        respx.get("https://fast.com/p1").mock(return_value=httpx.Response(200, text="1"))
        respx.get("https://fast.com/p2").mock(return_value=httpx.Response(200, text="2"))

        with patch("searchmuse.adapters.scrapers.httpx_scraper.asyncio.sleep") as mock_sleep:
            mock_sleep.return_value = None
            await adapter.scrape("https://fast.com/p1")
            await adapter.scrape("https://fast.com/p2")

        mock_sleep.assert_not_called()


# ---------------------------------------------------------------------------
# close
# ---------------------------------------------------------------------------


class TestClose:
    """close must be idempotent and release the underlying client."""

    async def test_close_before_any_request_is_noop(
        self, adapter: HttpxScraperAdapter
    ) -> None:
        # Should not raise even though the client was never initialised.
        await adapter.close()

    @respx.mock
    async def test_close_after_request_succeeds(self, adapter: HttpxScraperAdapter) -> None:
        respx.get("https://example.com/").mock(return_value=httpx.Response(200, text="ok"))
        await adapter.scrape("https://example.com/")

        await adapter.close()  # must not raise

    @respx.mock
    async def test_double_close_is_idempotent(self, adapter: HttpxScraperAdapter) -> None:
        respx.get("https://example.com/").mock(return_value=httpx.Response(200, text="ok"))
        await adapter.scrape("https://example.com/")

        await adapter.close()
        await adapter.close()  # second call must also not raise

    @respx.mock
    async def test_client_is_none_after_close(self, adapter: HttpxScraperAdapter) -> None:
        respx.get("https://example.com/").mock(return_value=httpx.Response(200, text="ok"))
        await adapter.scrape("https://example.com/")
        await adapter.close()

        assert adapter._client is None
