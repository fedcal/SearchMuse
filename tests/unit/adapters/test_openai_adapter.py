"""Unit tests for OpenAILLMAdapter.

The openai SDK is fully mocked so no real API calls are made.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from types import ModuleType, SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from searchmuse.domain.enums import RelevanceScore
from searchmuse.domain.errors import (
    LLMAuthenticationError,
    LLMConnectionError,
    LLMResponseError,
)
from searchmuse.domain.models import SearchQuery, Source
from searchmuse.infrastructure.config import LLMConfig

_CONFIG = LLMConfig(
    base_url="https://api.openai.com/v1",
    model="gpt-4o",
    strategy_temperature=0.3,
    assessment_temperature=0.1,
    synthesis_temperature=0.7,
    max_tokens=4096,
    timeout=120,
    provider="openai",
)

_NOW = datetime(2024, 6, 1, 12, 0, 0, tzinfo=UTC)


# Real exception classes for the mock SDK
class _AuthenticationError(Exception):
    pass


class _APIConnectionError(Exception):
    pass


class _APITimeoutError(Exception):
    pass


class _APIStatusError(Exception):
    pass


def _make_mock_sdk() -> ModuleType:
    """Build a mock openai module with real exception classes."""
    sdk = MagicMock(spec=[])
    sdk.AuthenticationError = _AuthenticationError
    sdk.APIConnectionError = _APIConnectionError
    sdk.APITimeoutError = _APITimeoutError
    sdk.APIStatusError = _APIStatusError
    return sdk


def _make_adapter(chat_return: str | None = None, chat_side_effect: Exception | None = None):
    """Create an OpenAILLMAdapter with mocked internals."""
    from searchmuse.adapters.llm._base import BaseLLMAdapter

    sdk = _make_mock_sdk()
    mock_client = MagicMock()

    if chat_side_effect is not None:
        mock_client.chat.completions.create = AsyncMock(side_effect=chat_side_effect)
    else:
        message = SimpleNamespace(content=chat_return or "")
        choice = SimpleNamespace(message=message)
        response = SimpleNamespace(choices=[choice])
        mock_client.chat.completions.create = AsyncMock(return_value=response)

    from searchmuse.adapters.llm.openai_adapter import OpenAILLMAdapter

    with patch.dict("sys.modules", {"openai": sdk}):
        adapter = OpenAILLMAdapter.__new__(OpenAILLMAdapter)
        BaseLLMAdapter.__init__(adapter, _CONFIG)
        adapter._sdk = sdk
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


class TestOpenAIAdapter:
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

    async def test_authentication_error_raises(self, sample_query: SearchQuery):
        adapter = _make_adapter(chat_side_effect=_AuthenticationError("bad key"))

        with pytest.raises(LLMAuthenticationError):
            await adapter.generate_search_strategy(sample_query, ())

    async def test_connection_error_raises(self, sample_query: SearchQuery):
        adapter = _make_adapter(chat_side_effect=_APIConnectionError("refused"))

        with pytest.raises(LLMConnectionError):
            await adapter.generate_search_strategy(sample_query, ())

    async def test_timeout_error_raises(self, sample_query: SearchQuery):
        adapter = _make_adapter(chat_side_effect=_APITimeoutError("timed out"))

        with pytest.raises(LLMConnectionError):
            await adapter.generate_search_strategy(sample_query, ())

    async def test_empty_response_raises(
        self, sample_query: SearchQuery, sample_source: Source,
    ):
        adapter = _make_adapter(chat_return="   ")

        with pytest.raises(LLMResponseError):
            await adapter.synthesize_answer(sample_query, (sample_source,))

    async def test_empty_choices_raises(self, sample_query: SearchQuery):
        """When response.choices is empty, should raise LLMResponseError."""
        from searchmuse.adapters.llm._base import BaseLLMAdapter
        from searchmuse.adapters.llm.openai_adapter import OpenAILLMAdapter

        sdk = _make_mock_sdk()
        mock_client = MagicMock()
        response = SimpleNamespace(choices=[])
        mock_client.chat.completions.create = AsyncMock(return_value=response)

        with patch.dict("sys.modules", {"openai": sdk}):
            adapter = OpenAILLMAdapter.__new__(OpenAILLMAdapter)
            BaseLLMAdapter.__init__(adapter, _CONFIG)
            adapter._sdk = sdk
            adapter._client = mock_client

        with pytest.raises(LLMResponseError):
            await adapter.generate_search_strategy(sample_query, ())
