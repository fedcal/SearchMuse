"""Unit tests for DuckDuckGoSearchAdapter.

All network I/O is eliminated by patching the private ``_run_ddgs_text``
helper and the ``asyncio.to_thread`` dispatcher so tests remain fast and
deterministic.

Tests cover:
- Successful multi-result searches return a tuple of SearchHit values
- Empty result lists return an empty tuple
- Any exception from DDGS is translated into a ScrapingError
- Adapter constructor defaults and per-call max_results override
- close() is a no-op coroutine
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from searchmuse.adapters.scrapers.duckduckgo_search import (
    DuckDuckGoSearchAdapter,
    _build_search_hit,
)
from searchmuse.domain.errors import ScrapingError
from searchmuse.domain.models import SearchHit

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SAMPLE_RAW_RESULT: dict[str, str] = {
    "href": "https://example.com/page",
    "title": "Example Page",
    "body": "A short snippet describing the page.",
}

_SAMPLE_RAW_RESULT_2: dict[str, str] = {
    "href": "https://other.org/article",
    "title": "Other Article",
    "body": "Second snippet text.",
}


# ---------------------------------------------------------------------------
# _build_search_hit unit tests
# ---------------------------------------------------------------------------


class TestBuildSearchHit:
    """Tests for the private _build_search_hit conversion helper."""

    def test_converts_all_fields(self) -> None:
        """All three keys are mapped to the correct SearchHit fields."""
        hit = _build_search_hit(_SAMPLE_RAW_RESULT)
        assert hit.url == "https://example.com/page"
        assert hit.title == "Example Page"
        assert hit.snippet == "A short snippet describing the page."

    def test_returns_search_hit_instance(self) -> None:
        """The return value is a SearchHit dataclass instance."""
        hit = _build_search_hit(_SAMPLE_RAW_RESULT)
        assert isinstance(hit, SearchHit)

    def test_missing_keys_default_to_empty_string(self) -> None:
        """Missing keys in the raw dict produce empty-string fields."""
        hit = _build_search_hit({})
        assert hit.url == ""
        assert hit.title == ""
        assert hit.snippet == ""

    def test_result_is_frozen(self) -> None:
        """SearchHit returned by the helper must be immutable."""
        import dataclasses

        hit = _build_search_hit(_SAMPLE_RAW_RESULT)
        with pytest.raises((dataclasses.FrozenInstanceError, AttributeError)):
            hit.url = "mutated"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# DuckDuckGoSearchAdapter.search tests
# ---------------------------------------------------------------------------


class TestDuckDuckGoSearchAdapterSearch:
    """Integration-level tests for the async search method."""

    @pytest.fixture()
    def adapter(self) -> DuckDuckGoSearchAdapter:
        """Default-configured adapter instance."""
        return DuckDuckGoSearchAdapter()

    async def test_search_returns_tuple_of_search_hits(
        self, adapter: DuckDuckGoSearchAdapter
    ) -> None:
        """search() wraps DDGS results in an immutable tuple of SearchHit."""
        raw = [_SAMPLE_RAW_RESULT, _SAMPLE_RAW_RESULT_2]
        with patch(
            "searchmuse.adapters.scrapers.duckduckgo_search.asyncio.to_thread",
            new=AsyncMock(return_value=raw),
        ):
            hits = await adapter.search("python asyncio")

        assert isinstance(hits, tuple)
        assert len(hits) == 2
        assert all(isinstance(h, SearchHit) for h in hits)

    async def test_search_hit_fields_match_raw_data(
        self, adapter: DuckDuckGoSearchAdapter
    ) -> None:
        """SearchHit fields correspond to href/title/body from the raw dict."""
        raw = [_SAMPLE_RAW_RESULT]
        with patch(
            "searchmuse.adapters.scrapers.duckduckgo_search.asyncio.to_thread",
            new=AsyncMock(return_value=raw),
        ):
            hits = await adapter.search("test query")

        first = hits[0]
        assert first.url == _SAMPLE_RAW_RESULT["href"]
        assert first.title == _SAMPLE_RAW_RESULT["title"]
        assert first.snippet == _SAMPLE_RAW_RESULT["body"]

    async def test_search_empty_results_returns_empty_tuple(
        self, adapter: DuckDuckGoSearchAdapter
    ) -> None:
        """An empty DDGS response produces an empty tuple, not an error."""
        with patch(
            "searchmuse.adapters.scrapers.duckduckgo_search.asyncio.to_thread",
            new=AsyncMock(return_value=[]),
        ):
            hits = await adapter.search("obscure query with no results")

        assert hits == ()

    async def test_search_raises_scraping_error_on_ddgs_exception(
        self, adapter: DuckDuckGoSearchAdapter
    ) -> None:
        """Any exception from the DDGS thread is re-raised as ScrapingError."""
        with patch(
            "searchmuse.adapters.scrapers.duckduckgo_search.asyncio.to_thread",
            new=AsyncMock(side_effect=RuntimeError("network failure")),
        ), pytest.raises(ScrapingError) as exc_info:
            await adapter.search("failing query")

        assert "DuckDuckGo search failed" in str(exc_info.value)

    async def test_scraping_error_url_is_the_query_string(
        self, adapter: DuckDuckGoSearchAdapter
    ) -> None:
        """ScrapingError.url is set to the query string for traceability."""
        query = "unique test query"
        with patch(
            "searchmuse.adapters.scrapers.duckduckgo_search.asyncio.to_thread",
            new=AsyncMock(side_effect=ConnectionError("timeout")),
        ), pytest.raises(ScrapingError) as exc_info:
            await adapter.search(query)

        assert exc_info.value.url == query

    async def test_search_passes_max_results_to_thread(
        self, adapter: DuckDuckGoSearchAdapter
    ) -> None:
        """max_results supplied to search() is forwarded to _run_ddgs_text."""
        captured: list[tuple] = []

        async def fake_to_thread(fn, *args, **kwargs):  # type: ignore[no-untyped-def]
            captured.append((args, kwargs))
            return []

        with patch(
            "searchmuse.adapters.scrapers.duckduckgo_search.asyncio.to_thread",
            side_effect=fake_to_thread,
        ):
            await adapter.search("query", max_results=7)

        # kwargs forwarded to _run_ddgs_text include max_results=7
        _, kw = captured[0]
        assert kw.get("max_results") == 7

    async def test_search_multiple_results_preserves_order(
        self, adapter: DuckDuckGoSearchAdapter
    ) -> None:
        """Results maintain the order returned by DDGS."""
        raw = [_SAMPLE_RAW_RESULT, _SAMPLE_RAW_RESULT_2]
        with patch(
            "searchmuse.adapters.scrapers.duckduckgo_search.asyncio.to_thread",
            new=AsyncMock(return_value=raw),
        ):
            hits = await adapter.search("ordered query")

        assert hits[0].url == _SAMPLE_RAW_RESULT["href"]
        assert hits[1].url == _SAMPLE_RAW_RESULT_2["href"]


# ---------------------------------------------------------------------------
# DuckDuckGoSearchAdapter.close tests
# ---------------------------------------------------------------------------


class TestDuckDuckGoSearchAdapterClose:
    """Tests for the no-op close() coroutine."""

    async def test_close_does_not_raise(self) -> None:
        """close() completes without raising any exception."""
        adapter = DuckDuckGoSearchAdapter()
        await adapter.close()  # must not raise


# ---------------------------------------------------------------------------
# Constructor configuration tests
# ---------------------------------------------------------------------------


class TestDuckDuckGoSearchAdapterConstructor:
    """Tests for constructor parameter storage."""

    def test_default_max_results_stored(self) -> None:
        """Default max_results is stored on the instance."""
        adapter = DuckDuckGoSearchAdapter(max_results=5)
        assert adapter._default_max_results == 5

    def test_custom_region_stored(self) -> None:
        """Custom region is stored correctly."""
        adapter = DuckDuckGoSearchAdapter(region="us-en")
        assert adapter._region == "us-en"

    def test_custom_safesearch_stored(self) -> None:
        """Custom safesearch value is stored correctly."""
        adapter = DuckDuckGoSearchAdapter(safesearch="off")
        assert adapter._safesearch == "off"

    def test_custom_timelimit_stored(self) -> None:
        """Custom timelimit is stored correctly."""
        adapter = DuckDuckGoSearchAdapter(timelimit="w")
        assert adapter._timelimit == "w"
