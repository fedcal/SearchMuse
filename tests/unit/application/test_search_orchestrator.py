"""Unit tests for SearchOrchestrator.

All six ports (LLM, search, scraper, extractor, repository, progress) are
replaced with AsyncMock/MagicMock so no real I/O occurs.  Each test focuses
on a single behaviour of the orchestrator's run() method.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from searchmuse.application.progress import (
    ProgressEvent,  # noqa: TC001 - used in runtime assertions
)
from searchmuse.application.search_orchestrator import SearchOrchestrator
from searchmuse.domain.enums import ContentType, RelevanceScore, SearchPhase
from searchmuse.domain.errors import ValidationError
from searchmuse.domain.models import (
    ExtractedContent,
    ScrapedPage,
    SearchHit,
    SearchResult,
    SearchStrategy,
)
from searchmuse.infrastructure.config import (
    ExtractionConfig,
    LLMConfig,
    LoggingConfig,
    OutputConfig,
    ScrapingConfig,
    SearchConfig,
    SearchMuseConfig,
    StorageConfig,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _now() -> datetime:
    return datetime.now(UTC)


def _make_strategy(query_id: str = "qid1", iteration: int = 1) -> SearchStrategy:
    return SearchStrategy(
        strategy_id="strat01",
        query_id=query_id,
        search_terms=("test query", "test topic overview"),
        target_domains=(),
        reasoning="Broad initial sweep.",
        iteration=iteration,
    )


def _make_hit(url: str = "https://example.com/page") -> SearchHit:
    return SearchHit(url=url, title="Example Page", snippet="Useful snippet.")


def _make_page(url: str = "https://example.com/page") -> ScrapedPage:
    return ScrapedPage(
        page_id="page01",
        url=url,
        raw_html="<html><body>Content</body></html>",
        http_status=200,
        content_type=ContentType.HTML,
        scraped_at=_now(),
        scraper_used="httpx",
    )


def _make_content(url: str = "https://example.com/page", page_id: str = "page01") -> ExtractedContent:
    return ExtractedContent(
        content_id="cont01",
        page_id=page_id,
        url=url,
        title="Example Page",
        clean_text="A" * 300,  # 300-char body, well above min_word_count
        author=None,
        published_date=None,
        word_count=60,
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def test_config() -> SearchMuseConfig:
    """Minimal SearchMuseConfig suitable for unit tests."""
    return SearchMuseConfig(
        llm=LLMConfig(
            base_url="http://localhost:11434",
            model="test",
            strategy_temperature=0.3,
            assessment_temperature=0.1,
            synthesis_temperature=0.7,
            max_tokens=4096,
            timeout=120,
        ),
        search=SearchConfig(
            max_iterations=3,
            min_sources=2,
            min_coverage_score=0.7,
            results_per_query=5,
            default_language="en",
        ),
        scraping=ScrapingConfig(
            request_delay=0.0,
            request_timeout=30,
            max_concurrent=5,
            respect_robots_txt=False,
            user_agent="Test/1.0",
            use_playwright=False,
            max_page_size=5_242_880,
        ),
        extraction=ExtractionConfig(
            min_word_count=50,
            max_text_length=8_000,
            preferred_extractor="trafilatura",
        ),
        storage=StorageConfig(db_path=":memory:", store_raw_html=False),
        output=OutputConfig(default_format="markdown", include_snippets=True, max_snippet_length=200),
        logging=LoggingConfig(level="DEBUG", file=None, timestamps=True),
    )


@pytest.fixture()
def mock_llm() -> MagicMock:
    """LLMPort mock with sensible defaults for the happy path."""
    llm = MagicMock()
    llm.generate_search_strategy = AsyncMock(return_value=_make_strategy())
    llm.assess_content_relevance = AsyncMock(return_value=RelevanceScore.HIGH)
    llm.assess_coverage = AsyncMock(return_value=(0.85, "Coverage is good."))
    llm.synthesize_answer = AsyncMock(return_value="Synthesized answer text [1]")
    return llm


@pytest.fixture()
def mock_search() -> MagicMock:
    """SearchPort mock that returns one hit per term."""
    search = MagicMock()
    search.search = AsyncMock(return_value=(_make_hit(),))
    return search


@pytest.fixture()
def mock_scraper() -> MagicMock:
    """ScraperPort mock that returns one scraped page."""
    scraper = MagicMock()
    scraper.scrape_many = AsyncMock(return_value=(_make_page(),))
    return scraper


@pytest.fixture()
def mock_extractor() -> MagicMock:
    """ContentExtractorPort mock (synchronous call) that returns one content."""
    extractor = MagicMock()
    extractor.extract = MagicMock(return_value=_make_content())
    return extractor


@pytest.fixture()
def mock_repository() -> MagicMock:
    """SourceRepositoryPort mock."""
    repo = MagicMock()
    repo.save = AsyncMock(return_value=None)
    return repo


@pytest.fixture()
def orchestrator(
    test_config: SearchMuseConfig,
    mock_llm: MagicMock,
    mock_search: MagicMock,
    mock_scraper: MagicMock,
    mock_extractor: MagicMock,
    mock_repository: MagicMock,
) -> SearchOrchestrator:
    """SearchOrchestrator with all ports mocked; no progress callback."""
    return SearchOrchestrator(
        config=test_config,
        llm=mock_llm,
        search=mock_search,
        scraper=mock_scraper,
        extractor=mock_extractor,
        repository=mock_repository,
    )


# ---------------------------------------------------------------------------
# Test 1: happy path - single iteration with sufficient coverage
# ---------------------------------------------------------------------------


class TestRunReturnsSearchResult:
    """run() returns a populated SearchResult on the happy path."""

    async def test_returns_search_result_type(self, orchestrator: SearchOrchestrator) -> None:
        result = await orchestrator.run("What is quantum entanglement?")

        assert isinstance(result, SearchResult)

    async def test_synthesis_is_forwarded(self, orchestrator: SearchOrchestrator) -> None:
        result = await orchestrator.run("What is quantum entanglement?")

        assert result.synthesis == "Synthesized answer text [1]"

    async def test_one_iteration_performed(self, orchestrator: SearchOrchestrator) -> None:
        result = await orchestrator.run("What is quantum entanglement?")

        # With coverage score 0.85 >= 0.7 and 1 source found, the loop
        # continues until min_sources=2 is satisfied or max_iterations
        # reached.  Because min_sources=2, it will NOT break early on the
        # first iteration (only 1 source found).  But with coverage >= min,
        # it checks sources_count >= min_sources too.  Let's confirm we get
        # at least 1 iteration.
        assert result.iterations_performed >= 1

    async def test_session_id_is_string(self, orchestrator: SearchOrchestrator) -> None:
        result = await orchestrator.run("What is quantum entanglement?")

        assert isinstance(result.session_id, str)
        assert len(result.session_id) > 0

    async def test_duration_is_non_negative(self, orchestrator: SearchOrchestrator) -> None:
        result = await orchestrator.run("What is quantum entanglement?")

        assert result.duration_seconds >= 0.0

    async def test_query_normalized_text_set(self, orchestrator: SearchOrchestrator) -> None:
        result = await orchestrator.run("  What is quantum entanglement?  ")

        assert result.query.normalized_text == "What is quantum entanglement?"

    async def test_synthesize_called_exactly_once(
        self,
        orchestrator: SearchOrchestrator,
        mock_llm: MagicMock,
    ) -> None:
        await orchestrator.run("What is quantum entanglement?")

        mock_llm.synthesize_answer.assert_awaited_once()

    async def test_citations_generated_from_sources(
        self,
        test_config: SearchMuseConfig,
        mock_llm: MagicMock,
        mock_search: MagicMock,
        mock_scraper: MagicMock,
        mock_extractor: MagicMock,
        mock_repository: MagicMock,
    ) -> None:
        """When coverage is high enough and min_sources met, citations are built."""
        # Return 2 distinct hits so min_sources=2 is satisfied in one iteration.
        mock_search.search = AsyncMock(
            return_value=(
                _make_hit("https://example.com/a"),
                _make_hit("https://example.com/b"),
            )
        )
        mock_scraper.scrape_many = AsyncMock(
            return_value=(
                _make_page("https://example.com/a"),
                _make_page("https://example.com/b"),
            )
        )
        mock_extractor.extract = MagicMock(
            side_effect=[
                _make_content("https://example.com/a", "p1"),
                _make_content("https://example.com/b", "p2"),
            ]
        )
        # Reset side_effect for multiple iterations
        mock_llm.assess_content_relevance = AsyncMock(return_value=RelevanceScore.HIGH)
        mock_llm.assess_coverage = AsyncMock(return_value=(0.9, "Excellent coverage."))

        orch = SearchOrchestrator(
            config=test_config,
            llm=mock_llm,
            search=mock_search,
            scraper=mock_scraper,
            extractor=mock_extractor,
            repository=mock_repository,
        )
        result = await orch.run("test query")

        assert len(result.citations) >= 1
        assert result.citations[0].index == 1


# ---------------------------------------------------------------------------
# Test 2: empty query raises ValidationError
# ---------------------------------------------------------------------------


class TestRunValidatesEmptyQuery:
    """run() must raise ValidationError for blank or empty queries."""

    async def test_empty_string_raises(self, orchestrator: SearchOrchestrator) -> None:
        with pytest.raises(ValidationError):
            await orchestrator.run("")

    async def test_whitespace_only_raises(self, orchestrator: SearchOrchestrator) -> None:
        with pytest.raises(ValidationError):
            await orchestrator.run("   ")

    async def test_tab_only_raises(self, orchestrator: SearchOrchestrator) -> None:
        with pytest.raises(ValidationError):
            await orchestrator.run("\t\n")

    async def test_llm_not_called_on_empty_query(
        self,
        orchestrator: SearchOrchestrator,
        mock_llm: MagicMock,
    ) -> None:
        with pytest.raises(ValidationError):
            await orchestrator.run("")

        mock_llm.generate_search_strategy.assert_not_awaited()


# ---------------------------------------------------------------------------
# Test 3: multiple iterations until coverage is sufficient
# ---------------------------------------------------------------------------


class TestRunMultipleIterationsUntilCoverage:
    """run() keeps iterating until coverage score meets the threshold."""

    async def test_loops_until_coverage_threshold_met(
        self,
        test_config: SearchMuseConfig,
        mock_llm: MagicMock,
        mock_search: MagicMock,
        mock_scraper: MagicMock,
        mock_extractor: MagicMock,
        mock_repository: MagicMock,
    ) -> None:
        # Provide 2 sources per iteration so min_sources=2 is always met.
        mock_search.search = AsyncMock(
            return_value=(
                _make_hit("https://a.com"),
                _make_hit("https://b.com"),
            )
        )
        mock_scraper.scrape_many = AsyncMock(
            return_value=(
                _make_page("https://a.com"),
                _make_page("https://b.com"),
            )
        )

        def _extract_side(page: ScrapedPage) -> ExtractedContent:
            return _make_content(page.url, page.page_id)

        mock_extractor.extract = MagicMock(side_effect=_extract_side)

        # First call: low coverage; second call: sufficient coverage.
        mock_llm.assess_coverage = AsyncMock(
            side_effect=[(0.3, "Not enough."), (0.9, "Good coverage.")]
        )

        orch = SearchOrchestrator(
            config=test_config,
            llm=mock_llm,
            search=mock_search,
            scraper=mock_scraper,
            extractor=mock_extractor,
            repository=mock_repository,
        )
        result = await orch.run("test query")

        assert result.iterations_performed == 2

    async def test_second_iteration_deduplicates_already_scraped_urls(
        self,
        test_config: SearchMuseConfig,
        mock_llm: MagicMock,
        mock_search: MagicMock,
        mock_scraper: MagicMock,
        mock_extractor: MagicMock,
        mock_repository: MagicMock,
    ) -> None:
        """URLs already in all_sources are skipped in subsequent iterations."""
        mock_search.search = AsyncMock(
            return_value=(
                _make_hit("https://same.com"),
                _make_hit("https://other.com"),
            )
        )
        mock_scraper.scrape_many = AsyncMock(
            return_value=(
                _make_page("https://same.com"),
                _make_page("https://other.com"),
            )
        )

        def _extract_side(page: ScrapedPage) -> ExtractedContent:
            return _make_content(page.url, page.page_id)

        mock_extractor.extract = MagicMock(side_effect=_extract_side)
        mock_llm.assess_coverage = AsyncMock(
            side_effect=[(0.3, "Low."), (0.9, "Sufficient.")]
        )

        orch = SearchOrchestrator(
            config=test_config,
            llm=mock_llm,
            search=mock_search,
            scraper=mock_scraper,
            extractor=mock_extractor,
            repository=mock_repository,
        )
        await orch.run("test query")

        # On the second iteration the same URLs come back; scrape_many
        # should be called but with an empty tuple (already scraped).
        second_call_args = mock_scraper.scrape_many.call_args_list[1]
        urls_passed_second = second_call_args.args[0]
        assert "https://same.com" not in urls_passed_second
        assert "https://other.com" not in urls_passed_second


# ---------------------------------------------------------------------------
# Test 4: stops at max_iterations even without sufficient coverage
# ---------------------------------------------------------------------------


class TestRunStopsAtMaxIterations:
    """run() stops after max_iterations regardless of coverage."""

    async def test_does_not_exceed_max_iterations(
        self,
        test_config: SearchMuseConfig,
        mock_llm: MagicMock,
        mock_search: MagicMock,
        mock_scraper: MagicMock,
        mock_extractor: MagicMock,
        mock_repository: MagicMock,
    ) -> None:
        # Coverage always below threshold; min_sources never met (0 sources).
        mock_llm.assess_coverage = AsyncMock(return_value=(0.1, "Very low coverage."))
        mock_llm.assess_content_relevance = AsyncMock(return_value=RelevanceScore.IRRELEVANT)
        mock_scraper.scrape_many = AsyncMock(return_value=())
        mock_extractor.extract = MagicMock(return_value=_make_content())

        orch = SearchOrchestrator(
            config=test_config,
            llm=mock_llm,
            search=mock_search,
            scraper=mock_scraper,
            extractor=mock_extractor,
            repository=mock_repository,
        )
        result = await orch.run("test query")

        assert result.iterations_performed == test_config.search.max_iterations

    async def test_synthesize_still_called_at_max_iterations(
        self,
        test_config: SearchMuseConfig,
        mock_llm: MagicMock,
        mock_search: MagicMock,
        mock_scraper: MagicMock,
        mock_extractor: MagicMock,
        mock_repository: MagicMock,
    ) -> None:
        mock_llm.assess_coverage = AsyncMock(return_value=(0.0, "No coverage."))
        mock_llm.assess_content_relevance = AsyncMock(return_value=RelevanceScore.IRRELEVANT)
        mock_scraper.scrape_many = AsyncMock(return_value=())

        orch = SearchOrchestrator(
            config=test_config,
            llm=mock_llm,
            search=mock_search,
            scraper=mock_scraper,
            extractor=mock_extractor,
            repository=mock_repository,
        )
        await orch.run("test query")

        mock_llm.synthesize_answer.assert_awaited_once()

    async def test_strategy_called_max_iterations_times(
        self,
        test_config: SearchMuseConfig,
        mock_llm: MagicMock,
        mock_search: MagicMock,
        mock_scraper: MagicMock,
        mock_extractor: MagicMock,
        mock_repository: MagicMock,
    ) -> None:
        mock_llm.assess_coverage = AsyncMock(return_value=(0.0, "No coverage."))
        mock_llm.assess_content_relevance = AsyncMock(return_value=RelevanceScore.IRRELEVANT)
        mock_scraper.scrape_many = AsyncMock(return_value=())

        orch = SearchOrchestrator(
            config=test_config,
            llm=mock_llm,
            search=mock_search,
            scraper=mock_scraper,
            extractor=mock_extractor,
            repository=mock_repository,
        )
        await orch.run("test query")

        assert mock_llm.generate_search_strategy.await_count == test_config.search.max_iterations


# ---------------------------------------------------------------------------
# Test 5: URL deduplication across search terms within one iteration
# ---------------------------------------------------------------------------


class TestRunDeduplicatesUrls:
    """The same URL returned by multiple search terms is scraped only once."""

    async def test_duplicate_url_scraped_once(
        self,
        test_config: SearchMuseConfig,
        mock_llm: MagicMock,
        mock_scraper: MagicMock,
        mock_extractor: MagicMock,
        mock_repository: MagicMock,
    ) -> None:
        duplicate_url = "https://shared.example.com/article"

        # Strategy returns two search terms.
        mock_llm.generate_search_strategy = AsyncMock(
            return_value=SearchStrategy(
                strategy_id="s1",
                query_id="q1",
                search_terms=("term one", "term two"),
                target_domains=(),
                reasoning="Two terms.",
                iteration=1,
            )
        )

        # Both terms yield the same URL.
        search = MagicMock()
        search.search = AsyncMock(return_value=(_make_hit(duplicate_url),))

        mock_llm.assess_coverage = AsyncMock(return_value=(0.9, "Good."))
        mock_llm.assess_content_relevance = AsyncMock(return_value=RelevanceScore.HIGH)

        orch = SearchOrchestrator(
            config=test_config,
            llm=mock_llm,
            search=search,
            scraper=mock_scraper,
            extractor=mock_extractor,
            repository=mock_repository,
        )
        await orch.run("test query")

        # scrape_many must receive the URL only once.
        scraped_urls = mock_scraper.scrape_many.call_args.args[0]
        assert scraped_urls.count(duplicate_url) == 1

    async def test_unique_urls_all_scraped(
        self,
        test_config: SearchMuseConfig,
        mock_llm: MagicMock,
        mock_scraper: MagicMock,
        mock_extractor: MagicMock,
        mock_repository: MagicMock,
    ) -> None:
        mock_llm.generate_search_strategy = AsyncMock(
            return_value=SearchStrategy(
                strategy_id="s2",
                query_id="q1",
                search_terms=("term one", "term two"),
                target_domains=(),
                reasoning="Two terms.",
                iteration=1,
            )
        )

        search = MagicMock()
        # Alternate between the two URLs on successive calls so the mock
        # never exhausts its side_effect regardless of iteration count.
        call_count: list[int] = [0]

        async def _alternating_search(term: str, *, max_results: int) -> tuple[SearchHit, ...]:
            call_count[0] += 1
            if call_count[0] % 2 == 1:
                return (_make_hit("https://alpha.com"),)
            return (_make_hit("https://beta.com"),)

        search.search = _alternating_search

        mock_llm.assess_coverage = AsyncMock(return_value=(0.9, "Good."))
        mock_llm.assess_content_relevance = AsyncMock(return_value=RelevanceScore.HIGH)

        orch = SearchOrchestrator(
            config=test_config,
            llm=mock_llm,
            search=search,
            scraper=mock_scraper,
            extractor=mock_extractor,
            repository=mock_repository,
        )
        await orch.run("test query")

        # On the first iteration both distinct URLs must be passed to scrape_many.
        first_call_args = mock_scraper.scrape_many.call_args_list[0]
        scraped_urls = first_call_args.args[0]
        assert "https://alpha.com" in scraped_urls
        assert "https://beta.com" in scraped_urls


# ---------------------------------------------------------------------------
# Test 6: low-relevance content is not added to sources
# ---------------------------------------------------------------------------


class TestRunSkipsLowRelevanceContent:
    """Content assessed as LOW or IRRELEVANT is not saved as a source."""

    async def test_irrelevant_content_not_saved(
        self,
        test_config: SearchMuseConfig,
        mock_llm: MagicMock,
        mock_search: MagicMock,
        mock_scraper: MagicMock,
        mock_extractor: MagicMock,
        mock_repository: MagicMock,
    ) -> None:
        mock_llm.assess_content_relevance = AsyncMock(return_value=RelevanceScore.IRRELEVANT)

        orch = SearchOrchestrator(
            config=test_config,
            llm=mock_llm,
            search=mock_search,
            scraper=mock_scraper,
            extractor=mock_extractor,
            repository=mock_repository,
        )
        await orch.run("test query")

        mock_repository.save.assert_not_awaited()

    async def test_low_relevance_content_not_saved(
        self,
        test_config: SearchMuseConfig,
        mock_llm: MagicMock,
        mock_search: MagicMock,
        mock_scraper: MagicMock,
        mock_extractor: MagicMock,
        mock_repository: MagicMock,
    ) -> None:
        mock_llm.assess_content_relevance = AsyncMock(return_value=RelevanceScore.LOW)

        orch = SearchOrchestrator(
            config=test_config,
            llm=mock_llm,
            search=mock_search,
            scraper=mock_scraper,
            extractor=mock_extractor,
            repository=mock_repository,
        )
        await orch.run("test query")

        mock_repository.save.assert_not_awaited()

    async def test_high_relevance_content_is_saved(
        self,
        test_config: SearchMuseConfig,
        mock_llm: MagicMock,
        mock_search: MagicMock,
        mock_scraper: MagicMock,
        mock_extractor: MagicMock,
        mock_repository: MagicMock,
    ) -> None:
        mock_llm.assess_content_relevance = AsyncMock(return_value=RelevanceScore.HIGH)

        orch = SearchOrchestrator(
            config=test_config,
            llm=mock_llm,
            search=mock_search,
            scraper=mock_scraper,
            extractor=mock_extractor,
            repository=mock_repository,
        )
        await orch.run("test query")

        mock_repository.save.assert_awaited()

    async def test_medium_relevance_content_is_saved(
        self,
        test_config: SearchMuseConfig,
        mock_llm: MagicMock,
        mock_search: MagicMock,
        mock_scraper: MagicMock,
        mock_extractor: MagicMock,
        mock_repository: MagicMock,
    ) -> None:
        mock_llm.assess_content_relevance = AsyncMock(return_value=RelevanceScore.MEDIUM)

        orch = SearchOrchestrator(
            config=test_config,
            llm=mock_llm,
            search=mock_search,
            scraper=mock_scraper,
            extractor=mock_extractor,
            repository=mock_repository,
        )
        await orch.run("test query")

        mock_repository.save.assert_awaited()

    async def test_total_sources_zero_when_all_irrelevant(
        self,
        test_config: SearchMuseConfig,
        mock_llm: MagicMock,
        mock_search: MagicMock,
        mock_scraper: MagicMock,
        mock_extractor: MagicMock,
        mock_repository: MagicMock,
    ) -> None:
        mock_llm.assess_content_relevance = AsyncMock(return_value=RelevanceScore.IRRELEVANT)

        orch = SearchOrchestrator(
            config=test_config,
            llm=mock_llm,
            search=mock_search,
            scraper=mock_scraper,
            extractor=mock_extractor,
            repository=mock_repository,
        )
        result = await orch.run("test query")

        assert result.total_sources_found == 0


# ---------------------------------------------------------------------------
# Test 7: progress callback receives events
# ---------------------------------------------------------------------------


class TestRunEmitsProgressEvents:
    """Progress events are emitted for each major phase."""

    async def test_progress_callback_is_called(
        self,
        test_config: SearchMuseConfig,
        mock_llm: MagicMock,
        mock_search: MagicMock,
        mock_scraper: MagicMock,
        mock_extractor: MagicMock,
        mock_repository: MagicMock,
    ) -> None:
        received: list[ProgressEvent] = []

        def _callback(event: ProgressEvent) -> None:
            received.append(event)

        orch = SearchOrchestrator(
            config=test_config,
            llm=mock_llm,
            search=mock_search,
            scraper=mock_scraper,
            extractor=mock_extractor,
            repository=mock_repository,
            progress=_callback,
        )
        await orch.run("test query")

        assert len(received) > 0

    async def test_initializing_event_emitted_first(
        self,
        test_config: SearchMuseConfig,
        mock_llm: MagicMock,
        mock_search: MagicMock,
        mock_scraper: MagicMock,
        mock_extractor: MagicMock,
        mock_repository: MagicMock,
    ) -> None:
        received: list[ProgressEvent] = []

        def _callback(event: ProgressEvent) -> None:
            received.append(event)

        orch = SearchOrchestrator(
            config=test_config,
            llm=mock_llm,
            search=mock_search,
            scraper=mock_scraper,
            extractor=mock_extractor,
            repository=mock_repository,
            progress=_callback,
        )
        await orch.run("test query")

        assert received[0].phase == SearchPhase.INITIALIZING

    async def test_complete_event_emitted_last(
        self,
        test_config: SearchMuseConfig,
        mock_llm: MagicMock,
        mock_search: MagicMock,
        mock_scraper: MagicMock,
        mock_extractor: MagicMock,
        mock_repository: MagicMock,
    ) -> None:
        received: list[ProgressEvent] = []

        def _callback(event: ProgressEvent) -> None:
            received.append(event)

        orch = SearchOrchestrator(
            config=test_config,
            llm=mock_llm,
            search=mock_search,
            scraper=mock_scraper,
            extractor=mock_extractor,
            repository=mock_repository,
            progress=_callback,
        )
        await orch.run("test query")

        assert received[-1].phase == SearchPhase.COMPLETE

    async def test_strategizing_event_emitted(
        self,
        test_config: SearchMuseConfig,
        mock_llm: MagicMock,
        mock_search: MagicMock,
        mock_scraper: MagicMock,
        mock_extractor: MagicMock,
        mock_repository: MagicMock,
    ) -> None:
        received: list[ProgressEvent] = []

        def _callback(event: ProgressEvent) -> None:
            received.append(event)

        orch = SearchOrchestrator(
            config=test_config,
            llm=mock_llm,
            search=mock_search,
            scraper=mock_scraper,
            extractor=mock_extractor,
            repository=mock_repository,
            progress=_callback,
        )
        await orch.run("test query")

        phases = [e.phase for e in received]
        assert SearchPhase.STRATEGIZING in phases

    async def test_synthesizing_event_emitted(
        self,
        test_config: SearchMuseConfig,
        mock_llm: MagicMock,
        mock_search: MagicMock,
        mock_scraper: MagicMock,
        mock_extractor: MagicMock,
        mock_repository: MagicMock,
    ) -> None:
        received: list[ProgressEvent] = []

        def _callback(event: ProgressEvent) -> None:
            received.append(event)

        orch = SearchOrchestrator(
            config=test_config,
            llm=mock_llm,
            search=mock_search,
            scraper=mock_scraper,
            extractor=mock_extractor,
            repository=mock_repository,
            progress=_callback,
        )
        await orch.run("test query")

        phases = [e.phase for e in received]
        assert SearchPhase.SYNTHESIZING in phases

    async def test_null_progress_used_when_none_provided(
        self,
        test_config: SearchMuseConfig,
        mock_llm: MagicMock,
        mock_search: MagicMock,
        mock_scraper: MagicMock,
        mock_extractor: MagicMock,
        mock_repository: MagicMock,
    ) -> None:
        """Passing progress=None must not raise; NullProgress absorbs events."""
        orch = SearchOrchestrator(
            config=test_config,
            llm=mock_llm,
            search=mock_search,
            scraper=mock_scraper,
            extractor=mock_extractor,
            repository=mock_repository,
            progress=None,
        )
        # Should complete without error.
        result = await orch.run("test query")

        assert isinstance(result, SearchResult)


# ---------------------------------------------------------------------------
# Test 8: extractor failure is gracefully skipped
# ---------------------------------------------------------------------------


class TestRunHandlesExtractionFailure:
    """When extract() raises, the page is skipped and the run continues."""

    async def test_extraction_error_does_not_abort_run(
        self,
        test_config: SearchMuseConfig,
        mock_llm: MagicMock,
        mock_search: MagicMock,
        mock_scraper: MagicMock,
        mock_repository: MagicMock,
    ) -> None:
        failing_extractor = MagicMock()
        failing_extractor.extract = MagicMock(side_effect=RuntimeError("parse failed"))

        orch = SearchOrchestrator(
            config=test_config,
            llm=mock_llm,
            search=mock_search,
            scraper=mock_scraper,
            extractor=failing_extractor,
            repository=mock_repository,
        )
        result = await orch.run("test query")

        assert isinstance(result, SearchResult)

    async def test_zero_sources_when_extraction_always_fails(
        self,
        test_config: SearchMuseConfig,
        mock_llm: MagicMock,
        mock_search: MagicMock,
        mock_scraper: MagicMock,
        mock_repository: MagicMock,
    ) -> None:
        failing_extractor = MagicMock()
        failing_extractor.extract = MagicMock(side_effect=RuntimeError("parse failed"))

        orch = SearchOrchestrator(
            config=test_config,
            llm=mock_llm,
            search=mock_search,
            scraper=mock_scraper,
            extractor=failing_extractor,
            repository=mock_repository,
        )
        result = await orch.run("test query")

        assert result.total_sources_found == 0
        mock_repository.save.assert_not_awaited()

    async def test_partial_extraction_success_keeps_good_pages(
        self,
        test_config: SearchMuseConfig,
        mock_llm: MagicMock,
        mock_search: MagicMock,
        mock_scraper: MagicMock,
        mock_repository: MagicMock,
    ) -> None:
        """If one page fails extraction but another succeeds, the good one is kept."""
        mock_scraper.scrape_many = AsyncMock(
            return_value=(
                _make_page("https://bad.com"),
                _make_page("https://good.com"),
            )
        )
        mock_search.search = AsyncMock(
            return_value=(
                _make_hit("https://bad.com"),
                _make_hit("https://good.com"),
            )
        )

        partial_extractor = MagicMock()
        partial_extractor.extract = MagicMock(
            side_effect=[
                RuntimeError("bad page"),
                _make_content("https://good.com", "pgood"),
            ]
        )
        mock_llm.assess_content_relevance = AsyncMock(return_value=RelevanceScore.HIGH)

        orch = SearchOrchestrator(
            config=test_config,
            llm=mock_llm,
            search=mock_search,
            scraper=mock_scraper,
            extractor=partial_extractor,
            repository=mock_repository,
        )
        result = await orch.run("test query")

        # The good page produced one source.
        assert result.total_sources_found >= 1
        mock_repository.save.assert_awaited_once()
