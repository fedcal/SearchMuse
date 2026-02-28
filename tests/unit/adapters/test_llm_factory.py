"""Unit tests for the LLM adapter factory."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from searchmuse.adapters.llm._factory import create_llm_adapter
from searchmuse.adapters.llm.ollama_adapter import OllamaLLMAdapter
from searchmuse.domain.errors import ConfigurationError
from searchmuse.infrastructure.config import LLMConfig


def _make_config(provider: str = "ollama", api_key: str | None = None) -> LLMConfig:
    return LLMConfig(
        base_url="http://localhost:11434",
        model="test-model",
        strategy_temperature=0.3,
        assessment_temperature=0.1,
        synthesis_temperature=0.7,
        max_tokens=4096,
        timeout=120,
        provider=provider,
        api_key=api_key,
    )


class TestCreateLLMAdapter:
    def test_ollama_returns_ollama_adapter(self):
        config = _make_config("ollama")

        adapter = create_llm_adapter(config)

        assert isinstance(adapter, OllamaLLMAdapter)

    def test_unknown_provider_raises_configuration_error(self):
        config = _make_config("unknown")

        with pytest.raises(ConfigurationError, match="Unknown LLM provider"):
            create_llm_adapter(config)

    def test_claude_without_key_raises_configuration_error(self):
        config = _make_config("claude")

        with patch(
            "searchmuse.infrastructure.api_key_resolver.resolve_api_key",
            return_value=None,
        ), pytest.raises(ConfigurationError, match="API key required"):
            create_llm_adapter(config)

    def test_claude_with_key_creates_adapter(self):
        config = _make_config("claude")
        mock_anthropic = MagicMock()

        with patch(
            "searchmuse.infrastructure.api_key_resolver.resolve_api_key",
            return_value="sk-ant-test",
        ), patch.dict("sys.modules", {"anthropic": mock_anthropic}):
            adapter = create_llm_adapter(config)

        assert adapter is not None
        assert type(adapter).__name__ == "ClaudeLLMAdapter"

    def test_openai_with_key_creates_adapter(self):
        config = _make_config("openai")
        mock_openai = MagicMock()

        with patch(
            "searchmuse.infrastructure.api_key_resolver.resolve_api_key",
            return_value="sk-openai-test",
        ), patch.dict("sys.modules", {"openai": mock_openai}):
            adapter = create_llm_adapter(config)

        assert adapter is not None
        assert type(adapter).__name__ == "OpenAILLMAdapter"

    def test_gemini_with_key_creates_adapter(self):
        config = _make_config("gemini")
        mock_google = MagicMock()
        mock_genai = MagicMock()
        mock_types = MagicMock()
        mock_google.genai = mock_genai

        with patch(
            "searchmuse.infrastructure.api_key_resolver.resolve_api_key",
            return_value="test-gemini-key",
        ), patch.dict("sys.modules", {
            "google": mock_google,
            "google.genai": mock_genai,
            "google.genai.types": mock_types,
        }):
            adapter = create_llm_adapter(config)

        assert adapter is not None
        assert type(adapter).__name__ == "GeminiLLMAdapter"

    def test_config_api_key_passed_to_resolver(self):
        config = _make_config("claude", api_key="from-yaml")
        mock_anthropic = MagicMock()

        with patch(
            "searchmuse.infrastructure.api_key_resolver.resolve_api_key",
            return_value="from-yaml",
        ) as mock_resolve, patch.dict("sys.modules", {"anthropic": mock_anthropic}):
            create_llm_adapter(config)

        mock_resolve.assert_called_once_with("claude", "from-yaml")

    def test_ollama_does_not_require_api_key(self):
        config = _make_config("ollama")

        adapter = create_llm_adapter(config)

        assert isinstance(adapter, OllamaLLMAdapter)
