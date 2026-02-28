"""Unit tests for API key resolver priority chain."""

from __future__ import annotations

from unittest.mock import patch

from searchmuse.infrastructure.api_key_resolver import resolve_api_key


class TestResolveApiKey:
    """resolve_api_key must check sources in priority order."""

    def test_universal_env_var_has_highest_priority(self):
        with patch.dict("os.environ", {
            "SEARCHMUSE_LLM_API_KEY": "universal-key",
            "ANTHROPIC_API_KEY": "specific-key",
        }):
            result = resolve_api_key("claude", "yaml-key")

        assert result == "universal-key"

    def test_provider_specific_env_var_second_priority(self):
        env = {"ANTHROPIC_API_KEY": "specific-key"}
        with patch.dict("os.environ", env, clear=False), patch.dict(
            "os.environ", {"SEARCHMUSE_LLM_API_KEY": ""}, clear=False,
        ):
            # Remove universal to test specific
            import os
            original = os.environ.pop("SEARCHMUSE_LLM_API_KEY", None)
            try:
                result = resolve_api_key("claude", "yaml-key")
            finally:
                if original is not None:
                    os.environ["SEARCHMUSE_LLM_API_KEY"] = original

        assert result == "specific-key"

    def test_openai_specific_env_var(self):
        with patch.dict("os.environ", {"OPENAI_API_KEY": "openai-key"}, clear=True):
            result = resolve_api_key("openai")

        assert result == "openai-key"

    def test_google_specific_env_var(self):
        with patch.dict("os.environ", {"GOOGLE_API_KEY": "google-key"}, clear=True):
            result = resolve_api_key("gemini")

        assert result == "google-key"

    def test_keyring_third_priority(self):
        with patch.dict("os.environ", {}, clear=True), patch(
            "searchmuse.infrastructure.keyring_store.get_api_key",
            return_value="keyring-key",
        ):
            result = resolve_api_key("claude")

        assert result == "keyring-key"

    def test_config_yaml_fourth_priority(self):
        with patch.dict("os.environ", {}, clear=True), patch(
            "searchmuse.infrastructure.keyring_store.get_api_key",
            return_value=None,
        ):
            result = resolve_api_key("claude", "yaml-key")

        assert result == "yaml-key"

    def test_returns_none_when_nothing_found(self):
        with patch.dict("os.environ", {}, clear=True), patch(
            "searchmuse.infrastructure.keyring_store.get_api_key",
            return_value=None,
        ):
            result = resolve_api_key("claude")

        assert result is None

    def test_ollama_returns_none_without_error(self):
        """Ollama doesn't have a provider-specific env var."""
        with patch.dict("os.environ", {}, clear=True), patch(
            "searchmuse.infrastructure.keyring_store.get_api_key",
            return_value=None,
        ):
            result = resolve_api_key("ollama")

        assert result is None

    def test_empty_env_var_is_not_used(self):
        """Empty string env vars should be treated as absent."""
        with patch.dict("os.environ", {
            "SEARCHMUSE_LLM_API_KEY": "",
            "ANTHROPIC_API_KEY": "",
        }, clear=True), patch(
            "searchmuse.infrastructure.keyring_store.get_api_key",
            return_value=None,
        ):
            result = resolve_api_key("claude", "yaml-key")

        assert result == "yaml-key"
