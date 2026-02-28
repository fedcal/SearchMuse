"""Unit tests for GeminiLLMAdapter.

The google-genai SDK is fully mocked so no real API calls are made.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from searchmuse.domain.enums import RelevanceScore
from searchmuse.domain.errors import (
    LLMConnectionError,
    LLMResponseError,
)
from searchmuse.domain.models import SearchQuery, Source
from searchmuse.infrastructure.config import LLMConfig

_CONFIG = LLMConfig(
    base_url="https://generativelanguage.googleapis.com",
    model="gemini-2.0-flash",
    strategy_temperature=0.3,
    assessment_temperature=0.1,
    synthesis_temperature=0.7,
    max_tokens=4096,
    timeout=120,
    provider="gemini",
)

_NOW = datetime(2024, 6, 1, 12, 0, 0, tzinfo=UTC)


# Real exception class for mock SDK
class _ClientError(Exception):
    pass


def _build_mock_genai():
    """Build mock google.genai and google.genai.types modules."""
    mock_genai = MagicMock(spec=[])
    mock_types = MagicMock(spec=[])
    # GenerateContentConfig must be callable and return a plain dict-like object
    mock_types.GenerateContentConfig = MagicMock(side_effect=lambda **kw: kw)
    mock_errors = MagicMock(spec=[])
    mock_errors.ClientError = _ClientError
    mock_genai.errors = mock_errors
    mock_genai.Client = MagicMock()

    mock_google = MagicMock(spec=[])
    mock_google.genai = mock_genai

    return mock_google, mock_genai, mock_types


def _make_adapter(chat_return: str | None = None, chat_side_effect: Exception | None = None):
    """Create a GeminiLLMAdapter with mocked internals."""
    from searchmuse.adapters.llm._base import BaseLLMAdapter

    mock_google, mock_genai, mock_types = _build_mock_genai()
    mock_client = MagicMock()
    mock_genai.Client.return_value = mock_client

    if chat_side_effect is not None:
        mock_client.aio.models.generate_content = AsyncMock(side_effect=chat_side_effect)
    else:
        response = SimpleNamespace(text=chat_return or "")
        mock_client.aio.models.generate_content = AsyncMock(return_value=response)

    from searchmuse.adapters.llm.gemini_adapter import GeminiLLMAdapter

    with patch.dict("sys.modules", {
        "google": mock_google,
        "google.genai": mock_genai,
        "google.genai.types": mock_types,
    }):
        adapter = GeminiLLMAdapter.__new__(GeminiLLMAdapter)
        BaseLLMAdapter.__init__(adapter, _CONFIG)
        adapter._genai = mock_genai
        adapter._genai_types = mock_types
        adapter._client = mock_client

    return adapter


@pytest.fixture()
def sample_query() -> SearchQuery:
    return SearchQuery(
        query_id="qid-001",
        raw_text="test query",
        normalized_text="test query",
        language="en",
        created_at=_NOW,
    )


@pytest.fixture()
def sample_source() -> Source:
    return Source(
        source_id="src-001",
        content_id="cid-001",
        url="https://example.com/article",
        title="Test Article",
        snippet="A test snippet.",
        relevance_score=RelevanceScore.HIGH,
        credibility_notes="Good source.",
        author=None,
        accessed_at=_NOW,
    )


class TestGeminiAdapter:
    async def test_generate_strategy_parses_json(self, sample_query: SearchQuery):
        payload = json.dumps({
            "search_terms": ["quantum"], "target_domains": [], "reasoning": "test",
        })
        adapter = _make_adapter(chat_return=payload)

        strategy = await adapter.generate_search_strategy(sample_query, ())

        assert strategy.search_terms == ("quantum",)

    async def test_synthesize_answer_returns_text(
        self, sample_query: SearchQuery, sample_source: Source,
    ):
        adapter = _make_adapter(chat_return="A comprehensive answer.")

        answer = await adapter.synthesize_answer(sample_query, (sample_source,))

        assert answer == "A comprehensive answer."

    async def test_connection_error_raises(self, sample_query: SearchQuery):
        adapter = _make_adapter(chat_side_effect=Exception("connection refused"))

        with pytest.raises(LLMConnectionError):
            await adapter.generate_search_strategy(sample_query, ())

    async def test_empty_response_raises(
        self, sample_query: SearchQuery, sample_source: Source,
    ):
        adapter = _make_adapter(chat_return="   ")

        with pytest.raises(LLMResponseError):
            await adapter.synthesize_answer(sample_query, (sample_source,))

    async def test_none_text_response_raises(
        self, sample_query: SearchQuery, sample_source: Source,
    ):
        """When response.text is None, the empty string → LLMResponseError."""
        adapter = _make_adapter(chat_return="")

        with pytest.raises(LLMResponseError):
            await adapter.synthesize_answer(sample_query, (sample_source,))
