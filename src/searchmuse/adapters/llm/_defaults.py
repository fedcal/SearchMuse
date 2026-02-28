"""Per-provider default values for model and base URL.

When the user does not customise model or base_url in the config YAML,
these defaults are used as sensible starting points for each provider.
"""

from __future__ import annotations

import dataclasses


@dataclasses.dataclass(frozen=True, slots=True)
class ProviderDefaults:
    """Immutable default settings for a single LLM provider."""

    model: str
    base_url: str
    requires_api_key: bool


PROVIDER_DEFAULTS: dict[str, ProviderDefaults] = {
    "ollama": ProviderDefaults(
        model="mistral",
        base_url="http://localhost:11434",
        requires_api_key=False,
    ),
    "claude": ProviderDefaults(
        model="claude-sonnet-4-6",
        base_url="https://api.anthropic.com",
        requires_api_key=True,
    ),
    "openai": ProviderDefaults(
        model="gpt-4o",
        base_url="https://api.openai.com/v1",
        requires_api_key=True,
    ),
    "gemini": ProviderDefaults(
        model="gemini-2.0-flash",
        base_url="https://generativelanguage.googleapis.com",
        requires_api_key=True,
    ),
}

SUPPORTED_PROVIDERS: frozenset[str] = frozenset(PROVIDER_DEFAULTS)
