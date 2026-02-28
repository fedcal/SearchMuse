"""API key resolution with priority chain.

Resolves the API key for a given LLM provider by checking sources
in descending priority order:

  1. ``SEARCHMUSE_LLM_API_KEY``  (universal env var)
  2. Provider-specific env var   (``ANTHROPIC_API_KEY``, ``OPENAI_API_KEY``, ``GOOGLE_API_KEY``)
  3. System keyring              (via :mod:`searchmuse.infrastructure.keyring_store`)
  4. ``api_key`` field from config YAML

Returns ``None`` when no key is found (acceptable for Ollama which
needs no authentication).
"""

from __future__ import annotations

import os

from searchmuse.infrastructure import keyring_store

_PROVIDER_ENV_VARS: dict[str, str] = {
    "claude": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "gemini": "GOOGLE_API_KEY",
}


def resolve_api_key(provider: str, config_api_key: str | None = None) -> str | None:
    """Return an API key for *provider* using the priority chain.

    Args:
        provider: The LLM provider name (e.g. ``"claude"``, ``"openai"``).
        config_api_key: Value from the YAML config's ``llm.api_key`` field.

    Returns:
        The resolved API key string, or ``None`` when no key is available.
    """
    # 1. Universal env var
    universal = os.environ.get("SEARCHMUSE_LLM_API_KEY")
    if universal:
        return universal

    # 2. Provider-specific env var
    env_var_name = _PROVIDER_ENV_VARS.get(provider)
    if env_var_name is not None:
        specific = os.environ.get(env_var_name)
        if specific:
            return specific

    # 3. System keyring
    from_keyring = keyring_store.get_api_key(provider)
    if from_keyring:
        return from_keyring

    # 4. Config YAML field
    if config_api_key:
        return config_api_key

    return None
