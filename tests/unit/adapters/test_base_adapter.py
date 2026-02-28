"""Unit tests for BaseLLMAdapter shared logic.

Uses a concrete StubAdapter whose _chat() returns a canned string,
allowing us to test prompt formatting, JSON parsing, and domain
object construction without any real LLM calls.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from searchmuse.adapters.llm._base import BaseLLMAdapter
from searchmuse.domain.enums import RelevanceScore
from searchmuse.domain.errors import LLMResponseError
from searchmuse.domain.models import (
    ExtractedContent,
    SearchIteration,
    SearchQuery,
    SearchStrategy,
    Source,
)
from searchmuse.infrastructure.config import LLMConfig

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_CONFIG = LLMConfig(
    base_url="http://localhost:11434",
    model="stub-model",
    strategy_temperature=0.3,
    assessment_temperature=0.1,
    synthesis_temperature=0.7,
    max_tokens=4096,
    timeout=120,
    provider="ollama",
)

_NOW = datetime(2024, 6, 1, 12, 0, 0, tzinfo=UTC)


class _StubAdapter(BaseLLMAdapter):
    """Minimal concrete adapter for testing BaseLLMAdapter logic."""

    def __init__(self, config: LLMConfig, *, response: str) -> None:
        super().__init__(config)
        self._chat_mock = AsyncMock(return_value=response)

    async def _chat(self, prompt: str, *, temperature: float) -> str:
        return await self._chat_mock(prompt, temperature=temperature)


def _stub(response: str) -> _StubAdapter:
    return _StubAdapter(_CONFIG, response=response)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def sample_query() -> SearchQuery:
    return SearchQuery(
        query_id="qid-001",
        raw_text="  What is quantum entanglement?  ",
        normalized_text="What is quantum entanglement?",
        language="en",
        created_at=_NOW,
    )


@pytest.fixture()
def sample_strategy(sample_query: SearchQuery) -> SearchStrategy:
    return SearchStrategy(
        strategy_id="sid-001",
        query_id=sample_query.query_id,
        search_terms=("quantum entanglement",),
        target_domains=("arxiv.org",),
        reasoning="Start with academic sources.",
        iteration=1,
    )


@pytest.fixture()
def sample_source() -> Source:
    return Source(
        source_id="src-001",
        content_id="cid-001",
        url="https://example.com/article",
        title="Quantum Entanglement Overview",
        snippet="A concise overview of quantum entanglement.",
        relevance_score=RelevanceScore.HIGH,
        credibility_notes="Peer-reviewed journal.",
        author="Alice Smith",
        accessed_at=_NOW,
    )


@pytest.fixture()
def sample_content() -> ExtractedContent:
    return ExtractedContent(
        content_id="cid-001",
        page_id="pid-001",
        url="https://example.com/article",
        title="Quantum Entanglement Overview",
        clean_text="Quantum entanglement is a phenomenon where particles are correlated.",
        author="Alice Smith",
        published_date="2024-01-01",
        word_count=12,
    )


@pytest.fixture()
def sample_iteration(sample_strategy: SearchStrategy, sample_source: Source) -> SearchIteration:
    return SearchIteration(
        iteration_number=1,
        strategy=sample_strategy,
        pages_scraped=5,
        contents_extracted=4,
        sources_found=(sample_source,),
        coverage_assessment="Partial coverage — needs more on applications.",
        sufficient=False,
    )


# ---------------------------------------------------------------------------
# generate_search_strategy
# ---------------------------------------------------------------------------


class TestGenerateSearchStrategy:
    async def test_returns_search_strategy(self, sample_query: SearchQuery):
        payload = json.dumps({
            "search_terms": ["quantum entanglement", "EPR paradox"],
            "target_domains": ["arxiv.org"],
            "reasoning": "Cover foundational papers.",
        })
        adapter = _stub(payload)

        strategy = await adapter.generate_search_strategy(sample_query, ())

        assert strategy.search_terms == ("quantum entanglement", "EPR paradox")
        assert strategy.target_domains == ("arxiv.org",)
        assert strategy.reasoning == "Cover foundational papers."

    async def test_iteration_number_increments(
        self, sample_query: SearchQuery, sample_iteration: SearchIteration,
    ):
        payload = json.dumps({
            "search_terms": ["test"], "target_domains": [], "reasoning": "second",
        })
        adapter = _stub(payload)

        strategy = await adapter.generate_search_strategy(
            sample_query, (sample_iteration, sample_iteration),
        )

        assert strategy.iteration == 3

    async def test_filters_blank_search_terms(self, sample_query: SearchQuery):
        payload = json.dumps({
            "search_terms": ["valid", "  ", ""],
            "target_domains": [],
            "reasoning": "test",
        })
        adapter = _stub(payload)

        strategy = await adapter.generate_search_strategy(sample_query, ())

        assert strategy.search_terms == ("valid",)

    async def test_raises_on_invalid_json(self, sample_query: SearchQuery):
        adapter = _stub("not json")

        with pytest.raises(LLMResponseError):
            await adapter.generate_search_strategy(sample_query, ())

    async def test_raises_on_missing_keys(self, sample_query: SearchQuery):
        payload = json.dumps({"search_terms": ["x"], "target_domains": []})
        adapter = _stub(payload)

        with pytest.raises(LLMResponseError):
            await adapter.generate_search_strategy(sample_query, ())


# ---------------------------------------------------------------------------
# assess_content_relevance
# ---------------------------------------------------------------------------


class TestAssessContentRelevance:
    @pytest.mark.parametrize(
        "raw_value, expected",
        [
            ("high", RelevanceScore.HIGH),
            ("medium", RelevanceScore.MEDIUM),
            ("low", RelevanceScore.LOW),
            ("irrelevant", RelevanceScore.IRRELEVANT),
        ],
    )
    async def test_maps_valid_values(
        self, raw_value, expected, sample_content: ExtractedContent, sample_query: SearchQuery,
    ):
        adapter = _stub(json.dumps({"relevance": raw_value}))

        score = await adapter.assess_content_relevance(sample_content, sample_query)

        assert score == expected

    async def test_raises_on_unknown_value(
        self, sample_content: ExtractedContent, sample_query: SearchQuery,
    ):
        adapter = _stub(json.dumps({"relevance": "unknown"}))

        with pytest.raises(LLMResponseError):
            await adapter.assess_content_relevance(sample_content, sample_query)


# ---------------------------------------------------------------------------
# assess_coverage
# ---------------------------------------------------------------------------


class TestAssessCoverage:
    async def test_returns_float_and_string(
        self, sample_query: SearchQuery, sample_source: Source,
    ):
        adapter = _stub(json.dumps({"coverage_score": 0.75, "assessment": "Good."}))

        score, narrative = await adapter.assess_coverage(sample_query, (sample_source,))

        assert isinstance(score, float)
        assert isinstance(narrative, str)
        assert score == pytest.approx(0.75)

    async def test_clamps_score_to_one(self, sample_query: SearchQuery):
        adapter = _stub(json.dumps({"coverage_score": 1.5, "assessment": "Over."}))

        score, _ = await adapter.assess_coverage(sample_query, ())

        assert score == pytest.approx(1.0)

    async def test_clamps_score_to_zero(self, sample_query: SearchQuery):
        adapter = _stub(json.dumps({"coverage_score": -0.3, "assessment": "Under."}))

        score, _ = await adapter.assess_coverage(sample_query, ())

        assert score == pytest.approx(0.0)

    async def test_raises_on_non_numeric_score(self, sample_query: SearchQuery):
        adapter = _stub(json.dumps({"coverage_score": "not-a-number", "assessment": "x"}))

        with pytest.raises(LLMResponseError):
            await adapter.assess_coverage(sample_query, ())


# ---------------------------------------------------------------------------
# synthesize_answer
# ---------------------------------------------------------------------------


class TestSynthesizeAnswer:
    async def test_returns_stripped_text(
        self, sample_query: SearchQuery, sample_source: Source,
    ):
        adapter = _stub("  A great answer.  ")

        answer = await adapter.synthesize_answer(sample_query, (sample_source,))

        assert answer == "A great answer."

    async def test_raises_on_empty_response(
        self, sample_query: SearchQuery, sample_source: Source,
    ):
        adapter = _stub("   ")

        with pytest.raises(LLMResponseError):
            await adapter.synthesize_answer(sample_query, (sample_source,))


# ---------------------------------------------------------------------------
# _parse_json
# ---------------------------------------------------------------------------


class TestParseJson:
    async def test_raises_when_json_is_list(self, sample_query: SearchQuery):
        adapter = _stub('["a", "b"]')

        with pytest.raises(LLMResponseError):
            await adapter.generate_search_strategy(sample_query, ())

    async def test_raises_when_json_is_scalar(self, sample_query: SearchQuery):
        adapter = _stub("42")

        with pytest.raises(LLMResponseError):
            await adapter.generate_search_strategy(sample_query, ())
