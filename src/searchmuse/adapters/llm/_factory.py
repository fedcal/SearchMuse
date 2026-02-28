"""Factory function for creating the appropriate LLM adapter.

Dispatches on ``config.llm.provider`` and resolves the API key via the
priority chain before constructing the adapter.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from searchmuse.adapters.llm._defaults import PROVIDER_DEFAULTS, SUPPORTED_PROVIDERS
from searchmuse.domain.errors import ConfigurationError

if TYPE_CHECKING:
    from searchmuse.adapters.llm._base import BaseLLMAdapter
    from searchmuse.infrastructure.config import LLMConfig


def create_llm_adapter(config: LLMConfig) -> BaseLLMAdapter:
    """Create the concrete LLM adapter for *config.provider*.

    Resolves the API key via
    :func:`~searchmuse.infrastructure.api_key_resolver.resolve_api_key`
    when the chosen provider requires one.

    Args:
        config: The LLM section of the application config.

    Returns:
        A fully initialised adapter that satisfies the ``LLMPort`` protocol.

    Raises:
        ConfigurationError: If the provider is unknown or a required API key
            is missing.
    """
    provider = config.provider.lower()

    if provider not in SUPPORTED_PROVIDERS:
        raise ConfigurationError(
            f"Unknown LLM provider {provider!r}. "
            f"Supported: {', '.join(sorted(SUPPORTED_PROVIDERS))}"
        )

    if provider == "ollama":
        from searchmuse.adapters.llm.ollama_adapter import OllamaLLMAdapter

        return OllamaLLMAdapter(config)

    # All non-Ollama providers require an API key.
    from searchmuse.infrastructure.api_key_resolver import resolve_api_key

    api_key = resolve_api_key(provider, config.api_key)
    defaults = PROVIDER_DEFAULTS[provider]

    if not api_key and defaults.requires_api_key:
        raise ConfigurationError(
            f"API key required for provider {provider!r}. "
            "Set SEARCHMUSE_LLM_API_KEY, the provider-specific env var, "
            "store it in the system keyring, or add api_key to your config YAML."
        )

    # api_key is guaranteed non-None here due to the check above.
    assert api_key is not None

    if provider == "claude":
        from searchmuse.adapters.llm.claude_adapter import ClaudeLLMAdapter

        return ClaudeLLMAdapter(config, api_key=api_key)

    if provider == "openai":
        from searchmuse.adapters.llm.openai_adapter import OpenAILLMAdapter

        return OpenAILLMAdapter(config, api_key=api_key)

    # provider == "gemini"
    from searchmuse.adapters.llm.gemini_adapter import GeminiLLMAdapter

    return GeminiLLMAdapter(config, api_key=api_key)
