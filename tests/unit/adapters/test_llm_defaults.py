"""Tests for searchmuse.adapters.llm._defaults."""

from searchmuse.adapters.llm._defaults import (
    PROVIDER_DEFAULTS,
    SUPPORTED_PROVIDERS,
    ProviderDefaults,
)


def test_supported_providers_contains_all():
    assert "ollama" in SUPPORTED_PROVIDERS
    assert "claude" in SUPPORTED_PROVIDERS
    assert "openai" in SUPPORTED_PROVIDERS
    assert "gemini" in SUPPORTED_PROVIDERS


def test_supported_providers_matches_defaults():
    assert frozenset(PROVIDER_DEFAULTS) == SUPPORTED_PROVIDERS


def test_provider_defaults_are_frozen():
    defaults = PROVIDER_DEFAULTS["ollama"]
    assert isinstance(defaults, ProviderDefaults)
    import pytest
    with pytest.raises(AttributeError):
        defaults.model = "other"  # type: ignore[misc]


def test_ollama_does_not_require_api_key():
    assert PROVIDER_DEFAULTS["ollama"].requires_api_key is False


def test_cloud_providers_require_api_key():
    for name in ("claude", "openai", "gemini"):
        assert PROVIDER_DEFAULTS[name].requires_api_key is True


def test_ollama_default_model():
    assert PROVIDER_DEFAULTS["ollama"].model == "mistral"


def test_all_providers_have_base_url():
    for name, defaults in PROVIDER_DEFAULTS.items():
        assert defaults.base_url, f"{name} has no base_url"
