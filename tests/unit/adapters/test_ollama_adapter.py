"""Unit tests for OllamaLLMAdapter.

The ollama.AsyncClient is fully mocked so no real Ollama server is required.
All async tests run automatically via asyncio_mode = "auto" (pytest-asyncio).
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from searchmuse.adapters.llm.ollama_adapter import OllamaLLMAdapter
from searchmuse.domain.enums import RelevanceScore
from searchmuse.domain.errors import LLMConnectionError, LLMResponseError
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

LLM_CONFIG = LLMConfig(
    base_url="http://localhost:11434",
    model="test-model",
    strategy_temperature=0.3,
    assessment_temperature=0.1,
    synthesis_temperature=0.7,
    max_tokens=4096,
    timeout=120,
    provider="ollama",
)

_NOW = datetime(2024, 6, 1, 12, 0, 0, tzinfo=UTC)


def _make_response(content: str) -> SimpleNamespace:
    """Build a minimal fake ollama response object with .message.content."""
    message = SimpleNamespace(content=content)
    return SimpleNamespace(message=message)


def _make_adapter(chat_return: str | Exception) -> OllamaLLMAdapter:
    """Return an OllamaLLMAdapter whose AsyncClient.chat is mocked.

    Args:
        chat_return: Either a string (the model response content) or an
            exception instance to raise when chat() is called.

    Returns:
        A fully mocked OllamaLLMAdapter ready for testing.
    """
    adapter = OllamaLLMAdapter(config=LLM_CONFIG)
    if isinstance(chat_return, Exception):
        adapter._client.chat = AsyncMock(side_effect=chat_return)
    else:
        adapter._client.chat = AsyncMock(
            return_value=_make_response(chat_return)
        )
    return adapter


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
    """generate_search_strategy must parse JSON and return a SearchStrategy."""

    async def test_returns_search_strategy_with_correct_fields(
        self, sample_query: SearchQuery
    ) -> None:
        payload = json.dumps(
            {
                "search_terms": ["quantum entanglement", "EPR paradox"],
                "target_domains": ["arxiv.org", "wikipedia.org"],
                "reasoning": "Cover foundational papers and encyclopaedia.",
            }
        )
        adapter = _make_adapter(payload)

        strategy = await adapter.generate_search_strategy(sample_query, ())

        assert strategy.search_terms == ("quantum entanglement", "EPR paradox")
        assert strategy.target_domains == ("arxiv.org", "wikipedia.org")
        assert strategy.reasoning == "Cover foundational papers and encyclopaedia."

    async def test_iteration_number_is_one_for_first_call(
        self, sample_query: SearchQuery
    ) -> None:
        payload = json.dumps(
            {"search_terms": ["test"], "target_domains": [], "reasoning": "first"}
        )
        adapter = _make_adapter(payload)

        strategy = await adapter.generate_search_strategy(sample_query, ())

        assert strategy.iteration == 1

    async def test_iteration_number_increments_with_previous_iterations(
        self,
        sample_query: SearchQuery,
        sample_iteration: SearchIteration,
    ) -> None:
        payload = json.dumps(
            {"search_terms": ["test"], "target_domains": [], "reasoning": "second"}
        )
        adapter = _make_adapter(payload)

        strategy = await adapter.generate_search_strategy(
            sample_query, (sample_iteration, sample_iteration)
        )

        assert strategy.iteration == 3

    async def test_strategy_query_id_matches_query(self, sample_query: SearchQuery) -> None:
        payload = json.dumps(
            {"search_terms": ["x"], "target_domains": [], "reasoning": "r"}
        )
        adapter = _make_adapter(payload)

        strategy = await adapter.generate_search_strategy(sample_query, ())

        assert strategy.query_id == sample_query.query_id

    async def test_strategy_id_is_non_empty_string(self, sample_query: SearchQuery) -> None:
        payload = json.dumps(
            {"search_terms": ["x"], "target_domains": [], "reasoning": "r"}
        )
        adapter = _make_adapter(payload)

        strategy = await adapter.generate_search_strategy(sample_query, ())

        assert isinstance(strategy.strategy_id, str)
        assert strategy.strategy_id

    async def test_raises_llm_response_error_on_invalid_json(
        self, sample_query: SearchQuery
    ) -> None:
        adapter = _make_adapter("this is not JSON at all")

        with pytest.raises(LLMResponseError):
            await adapter.generate_search_strategy(sample_query, ())

    async def test_raises_llm_response_error_on_missing_keys(
        self, sample_query: SearchQuery
    ) -> None:
        # Missing "reasoning" key.
        payload = json.dumps({"search_terms": ["x"], "target_domains": []})
        adapter = _make_adapter(payload)

        with pytest.raises(LLMResponseError):
            await adapter.generate_search_strategy(sample_query, ())

    async def test_raises_llm_connection_error_on_connection_failure(
        self, sample_query: SearchQuery
    ) -> None:
        adapter = _make_adapter(ConnectionError("refused"))

        with pytest.raises(LLMConnectionError):
            await adapter.generate_search_strategy(sample_query, ())

    async def test_raises_llm_connection_error_on_timeout(
        self, sample_query: SearchQuery
    ) -> None:
        adapter = _make_adapter(TimeoutError("timed out"))

        with pytest.raises(LLMConnectionError):
            await adapter.generate_search_strategy(sample_query, ())

    async def test_filters_blank_search_terms(self, sample_query: SearchQuery) -> None:
        payload = json.dumps(
            {
                "search_terms": ["valid term", "  ", ""],
                "target_domains": [],
                "reasoning": "test",
            }
        )
        adapter = _make_adapter(payload)

        strategy = await adapter.generate_search_strategy(sample_query, ())

        assert strategy.search_terms == ("valid term",)


# ---------------------------------------------------------------------------
# assess_content_relevance
# ---------------------------------------------------------------------------


class TestAssessContentRelevance:
    """assess_content_relevance must map the model JSON to a RelevanceScore."""

    @pytest.mark.parametrize(
        "raw_value, expected",
        [
            ("high", RelevanceScore.HIGH),
            ("medium", RelevanceScore.MEDIUM),
            ("low", RelevanceScore.LOW),
            ("irrelevant", RelevanceScore.IRRELEVANT),
        ],
    )
    async def test_maps_valid_relevance_values(
        self,
        raw_value: str,
        expected: RelevanceScore,
        sample_content: ExtractedContent,
        sample_query: SearchQuery,
    ) -> None:
        payload = json.dumps({"relevance": raw_value})
        adapter = _make_adapter(payload)

        score = await adapter.assess_content_relevance(sample_content, sample_query)

        assert score == expected

    async def test_raises_llm_response_error_on_unknown_value(
        self,
        sample_content: ExtractedContent,
        sample_query: SearchQuery,
    ) -> None:
        payload = json.dumps({"relevance": "totally_unknown_value"})
        adapter = _make_adapter(payload)

        with pytest.raises(LLMResponseError):
            await adapter.assess_content_relevance(sample_content, sample_query)

    async def test_raises_llm_response_error_on_invalid_json(
        self,
        sample_content: ExtractedContent,
        sample_query: SearchQuery,
    ) -> None:
        adapter = _make_adapter("{bad json")

        with pytest.raises(LLMResponseError):
            await adapter.assess_content_relevance(sample_content, sample_query)

    async def test_raises_llm_response_error_on_missing_relevance_key(
        self,
        sample_content: ExtractedContent,
        sample_query: SearchQuery,
    ) -> None:
        payload = json.dumps({"score": "high"})  # wrong key name
        adapter = _make_adapter(payload)

        with pytest.raises(LLMResponseError):
            await adapter.assess_content_relevance(sample_content, sample_query)

    async def test_raises_llm_connection_error_on_connection_failure(
        self,
        sample_content: ExtractedContent,
        sample_query: SearchQuery,
    ) -> None:
        adapter = _make_adapter(ConnectionError("refused"))

        with pytest.raises(LLMConnectionError):
            await adapter.assess_content_relevance(sample_content, sample_query)


# ---------------------------------------------------------------------------
# assess_coverage
# ---------------------------------------------------------------------------


class TestAssessCoverage:
    """assess_coverage must return a (float, str) tuple with a clamped score."""

    async def test_returns_float_and_string_tuple(
        self,
        sample_query: SearchQuery,
        sample_source: Source,
    ) -> None:
        payload = json.dumps({"coverage_score": 0.75, "assessment": "Good coverage."})
        adapter = _make_adapter(payload)

        result = await adapter.assess_coverage(sample_query, (sample_source,))

        assert isinstance(result, tuple)
        score, narrative = result
        assert isinstance(score, float)
        assert isinstance(narrative, str)

    async def test_score_value_is_correct(
        self,
        sample_query: SearchQuery,
        sample_source: Source,
    ) -> None:
        payload = json.dumps({"coverage_score": 0.6, "assessment": "Partial."})
        adapter = _make_adapter(payload)

        score, _ = await adapter.assess_coverage(sample_query, (sample_source,))

        assert score == pytest.approx(0.6)

    async def test_score_is_clamped_to_one(
        self,
        sample_query: SearchQuery,
        sample_source: Source,
    ) -> None:
        payload = json.dumps({"coverage_score": 1.5, "assessment": "Over 100%."})
        adapter = _make_adapter(payload)

        score, _ = await adapter.assess_coverage(sample_query, (sample_source,))

        assert score == pytest.approx(1.0)

    async def test_score_is_clamped_to_zero(
        self,
        sample_query: SearchQuery,
    ) -> None:
        payload = json.dumps({"coverage_score": -0.3, "assessment": "Negative."})
        adapter = _make_adapter(payload)

        score, _ = await adapter.assess_coverage(sample_query, ())

        assert score == pytest.approx(0.0)

    async def test_narrative_is_returned(
        self,
        sample_query: SearchQuery,
    ) -> None:
        narrative_text = "Need more detail on applications."
        payload = json.dumps({"coverage_score": 0.4, "assessment": narrative_text})
        adapter = _make_adapter(payload)

        _, narrative = await adapter.assess_coverage(sample_query, ())

        assert narrative == narrative_text

    async def test_raises_llm_response_error_on_invalid_json(
        self,
        sample_query: SearchQuery,
    ) -> None:
        adapter = _make_adapter("not json")

        with pytest.raises(LLMResponseError):
            await adapter.assess_coverage(sample_query, ())

    async def test_raises_llm_response_error_on_missing_keys(
        self,
        sample_query: SearchQuery,
    ) -> None:
        payload = json.dumps({"coverage_score": 0.5})  # missing "assessment"
        adapter = _make_adapter(payload)

        with pytest.raises(LLMResponseError):
            await adapter.assess_coverage(sample_query, ())

    async def test_raises_llm_response_error_on_non_numeric_score(
        self,
        sample_query: SearchQuery,
    ) -> None:
        payload = json.dumps({"coverage_score": "not-a-number", "assessment": "x"})
        adapter = _make_adapter(payload)

        with pytest.raises(LLMResponseError):
            await adapter.assess_coverage(sample_query, ())

    async def test_raises_llm_connection_error_on_connection_failure(
        self,
        sample_query: SearchQuery,
    ) -> None:
        adapter = _make_adapter(ConnectionError("refused"))

        with pytest.raises(LLMConnectionError):
            await adapter.assess_coverage(sample_query, ())


# ---------------------------------------------------------------------------
# synthesize_answer
# ---------------------------------------------------------------------------


class TestSynthesizeAnswer:
    """synthesize_answer must return the model's plain-text response."""

    async def test_returns_non_empty_string(
        self,
        sample_query: SearchQuery,
        sample_source: Source,
    ) -> None:
        adapter = _make_adapter("Quantum entanglement is a phenomenon where particles share state.")

        answer = await adapter.synthesize_answer(sample_query, (sample_source,))

        assert isinstance(answer, str)
        assert answer

    async def test_returns_stripped_text(
        self,
        sample_query: SearchQuery,
        sample_source: Source,
    ) -> None:
        adapter = _make_adapter("  Answer with surrounding whitespace.  ")

        answer = await adapter.synthesize_answer(sample_query, (sample_source,))

        assert answer == "Answer with surrounding whitespace."

    async def test_raises_llm_response_error_on_empty_response(
        self,
        sample_query: SearchQuery,
        sample_source: Source,
    ) -> None:
        adapter = _make_adapter("   ")  # whitespace-only is treated as empty

        with pytest.raises(LLMResponseError):
            await adapter.synthesize_answer(sample_query, (sample_source,))

    async def test_raises_llm_connection_error_on_connection_failure(
        self,
        sample_query: SearchQuery,
        sample_source: Source,
    ) -> None:
        adapter = _make_adapter(ConnectionError("refused"))

        with pytest.raises(LLMConnectionError):
            await adapter.synthesize_answer(sample_query, (sample_source,))

    async def test_raises_llm_connection_error_on_unexpected_exception(
        self,
        sample_query: SearchQuery,
        sample_source: Source,
    ) -> None:
        """Any unexpected exception from ollama.chat must become LLMConnectionError."""
        adapter = _make_adapter(RuntimeError("unexpected"))

        with pytest.raises(LLMConnectionError):
            await adapter.synthesize_answer(sample_query, (sample_source,))

    async def test_works_with_no_sources(self, sample_query: SearchQuery) -> None:
        adapter = _make_adapter("No sources available but here is what I know.")

        answer = await adapter.synthesize_answer(sample_query, ())

        assert "No sources" in answer or answer


# ---------------------------------------------------------------------------
# _chat — response structure validation
# ---------------------------------------------------------------------------


class TestChatHelper:
    """_chat must raise LLMResponseError when the response object is malformed."""

    async def test_raises_llm_response_error_on_missing_message_attr(
        self, sample_query: SearchQuery
    ) -> None:
        """Simulate a response object that has no .message attribute."""
        bad_response = SimpleNamespace()  # no .message attribute
        adapter = OllamaLLMAdapter(config=LLM_CONFIG)
        adapter._client.chat = AsyncMock(return_value=bad_response)

        # _chat is called internally; we trigger it via a public method.
        adapter._client.chat = AsyncMock(return_value=bad_response)

        with pytest.raises(LLMResponseError):
            await adapter.generate_search_strategy(sample_query, ())

    async def test_raises_llm_connection_error_on_timeout_error(
        self, sample_query: SearchQuery
    ) -> None:
        adapter = OllamaLLMAdapter(config=LLM_CONFIG)
        adapter._client.chat = AsyncMock(side_effect=TimeoutError("timed out"))

        with pytest.raises(LLMConnectionError):
            await adapter.generate_search_strategy(sample_query, ())


# ---------------------------------------------------------------------------
# _parse_json — edge cases
# ---------------------------------------------------------------------------


class TestParseJson:
    """_parse_json must reject non-dict JSON and flag missing required keys."""

    async def test_raises_when_json_is_list(self, sample_query: SearchQuery) -> None:
        adapter = _make_adapter('["a", "b", "c"]')  # valid JSON but not a dict

        with pytest.raises(LLMResponseError):
            await adapter.generate_search_strategy(sample_query, ())

    async def test_raises_when_json_is_scalar(self, sample_query: SearchQuery) -> None:
        adapter = _make_adapter("42")

        with pytest.raises(LLMResponseError):
            await adapter.generate_search_strategy(sample_query, ())
