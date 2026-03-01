"""Shared pytest fixtures for the SearchMuse test suite."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from searchmuse.domain.enums import ContentType, RelevanceScore, SearchPhase
from searchmuse.domain.models import (
    Citation,
    ExtractedContent,
    ScrapedPage,
    SearchHit,
    SearchIteration,
    SearchQuery,
    SearchResult,
    SearchState,
    SearchStrategy,
    Source,
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


def _short_id() -> str:
    """Return an 8-character hex ID."""
    return uuid4().hex[:8]


def _now() -> datetime:
    """Return the current UTC datetime."""
    return datetime.now(UTC)


@pytest.fixture()
def sample_query() -> SearchQuery:
    """A valid, frozen SearchQuery for use in tests."""
    return SearchQuery(
        query_id=_short_id(),
        raw_text="  What is quantum entanglement?  ",
        normalized_text="What is quantum entanglement?",
        language="en",
        created_at=_now(),
    )


@pytest.fixture()
def sample_strategy(sample_query: SearchQuery) -> SearchStrategy:
    """A valid, frozen SearchStrategy for use in tests."""
    return SearchStrategy(
        strategy_id=_short_id(),
        query_id=sample_query.query_id,
        search_terms=("quantum entanglement", "entanglement physics definition"),
        target_domains=("arxiv.org", "wikipedia.org"),
        reasoning="Starting with authoritative scientific sources.",
        iteration=1,
    )


@pytest.fixture()
def sample_source() -> Source:
    """A valid, frozen Source for use in tests."""
    return Source(
        source_id=_short_id(),
        content_id=_short_id(),
        url="https://en.wikipedia.org/wiki/Quantum_entanglement",
        title="Quantum entanglement - Wikipedia",
        snippet="Quantum entanglement is a phenomenon in quantum mechanics...",
        relevance_score=RelevanceScore.HIGH,
        credibility_notes="Well-established encyclopaedia entry with citations.",
        author=None,
        accessed_at=_now(),
    )


@pytest.fixture()
def sample_citation(sample_source: Source) -> Citation:
    """A valid, frozen Citation derived from sample_source."""
    return Citation(
        citation_id=_short_id(),
        source_id=sample_source.source_id,
        index=1,
        formatted_text=(
            "[1] Quantum entanglement - Wikipedia. "
            "https://en.wikipedia.org/wiki/Quantum_entanglement"
        ),
        url=sample_source.url,
    )


@pytest.fixture()
def sample_search_state(
    sample_query: SearchQuery,
) -> SearchState:
    """An initial SearchState in the INITIALIZING phase with no iterations."""
    return SearchState(
        session_id=_short_id(),
        query=sample_query,
        iterations=(),
        all_sources=(),
        phase=SearchPhase.INITIALIZING,
    )


@pytest.fixture()
def sample_iteration(
    sample_strategy: SearchStrategy,
    sample_source: Source,
) -> SearchIteration:
    """A completed SearchIteration containing one source."""
    return SearchIteration(
        iteration_number=1,
        strategy=sample_strategy,
        pages_scraped=5,
        contents_extracted=4,
        sources_found=(sample_source,),
        coverage_assessment="Basic definition covered; need more on applications.",
        sufficient=False,
    )


@pytest.fixture()
def sample_search_hit() -> SearchHit:
    """A valid SearchHit for use in tests."""
    return SearchHit(
        url="https://example.com/article",
        title="Example Article",
        snippet="An article about quantum entanglement.",
    )


@pytest.fixture()
def sample_scraped_page() -> ScrapedPage:
    """A valid ScrapedPage for use in tests."""
    return ScrapedPage(
        page_id=_short_id(),
        url="https://example.com/article",
        raw_html="<html><body><p>Quantum entanglement is a phenomenon.</p></body></html>",
        http_status=200,
        content_type=ContentType.HTML,
        scraped_at=_now(),
        scraper_used="httpx",
    )


@pytest.fixture()
def sample_extracted_content(sample_scraped_page: ScrapedPage) -> ExtractedContent:
    """A valid ExtractedContent for use in tests."""
    text = "Quantum entanglement is a phenomenon " * 20
    return ExtractedContent(
        content_id=_short_id(),
        page_id=sample_scraped_page.page_id,
        url=sample_scraped_page.url,
        title="Quantum Entanglement Explained",
        clean_text=text,
        author="Jane Doe",
        published_date="2024-01-15",
        word_count=len(text.split()),
    )


@pytest.fixture()
def sample_search_result(
    sample_query: SearchQuery,
    sample_citation: Citation,
) -> SearchResult:
    """A valid SearchResult for use in tests."""
    return SearchResult(
        session_id=_short_id(),
        query=sample_query,
        synthesis="Quantum entanglement is a correlation between particles [1].",
        citations=(sample_citation,),
        total_sources_found=3,
        iterations_performed=2,
        duration_seconds=15.5,
    )


@pytest.fixture()
def test_config(tmp_path: object) -> SearchMuseConfig:
    """A valid SearchMuseConfig for testing."""
    return SearchMuseConfig(
        llm=LLMConfig(
            base_url="http://localhost:11434",
            model="test-model",
            strategy_temperature=0.3,
            assessment_temperature=0.1,
            synthesis_temperature=0.7,
            max_tokens=4096,
            timeout=120,
            provider="ollama",
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
            max_page_size=5242880,
        ),
        extraction=ExtractionConfig(
            min_word_count=50,
            max_text_length=8000,
            preferred_extractor="trafilatura",
        ),
        storage=StorageConfig(
            db_path=":memory:",
            store_raw_html=False,
        ),
        output=OutputConfig(
            default_format="markdown",
            include_snippets=True,
            max_snippet_length=200,
        ),
        logging=LoggingConfig(
            level="DEBUG",
            file=None,
            timestamps=True,
            ui_language="en",
        ),
    )
