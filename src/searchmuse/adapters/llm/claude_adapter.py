"""Claude (Anthropic) LLM adapter implementing the LLMPort protocol.

Uses the ``anthropic`` async client.  The SDK is imported lazily so that
the package is only required when the user selects ``provider: claude``.

Error handling contract:
  - LLMAuthenticationError: raised when the API key is rejected.
  - LLMConnectionError:     raised when the API cannot be reached.
  - LLMResponseError:       raised when a response cannot be parsed.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from searchmuse.adapters.llm._base import BaseLLMAdapter
from searchmuse.domain.errors import (
    LLMAuthenticationError,
    LLMConnectionError,
    LLMResponseError,
)

if TYPE_CHECKING:
    from searchmuse.infrastructure.config import LLMConfig

logger: logging.Logger = logging.getLogger(__name__)


class ClaudeLLMAdapter(BaseLLMAdapter):
    """Concrete LLM adapter backed by the Anthropic Messages API."""

    def __init__(self, config: LLMConfig, *, api_key: str) -> None:
        super().__init__(config)
        try:
            import anthropic
        except ImportError as exc:
            raise ImportError(
                "The 'anthropic' package is required for the Claude provider. "
                "Install it with: pip install 'searchmuse[claude]'"
            ) from exc

        self._sdk: Any = anthropic
        self._client = anthropic.AsyncAnthropic(
            api_key=api_key,
            max_retries=0,
            timeout=config.timeout,
        )
        logger.debug(
            "ClaudeLLMAdapter initialised: model=%r",
            config.model,
        )

    async def _chat(self, prompt: str, *, temperature: float) -> str:
        """Send a single-turn message to the Anthropic Messages API."""
        sdk = self._sdk

        try:
            response = await self._client.messages.create(
                model=self._config.model,
                max_tokens=self._config.max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}],
            )
        except sdk.AuthenticationError as exc:
            raise LLMAuthenticationError(
                "Anthropic API key is invalid or expired",
                model=self._config.model,
                detail=str(exc),
            ) from exc
        except (sdk.APIConnectionError, sdk.APITimeoutError) as exc:
            logger.error("Claude connection error: %s", exc)
            raise LLMConnectionError(
                "Failed to connect to Anthropic API",
                model=self._config.model,
                detail=str(exc),
            ) from exc
        except sdk.APIStatusError as exc:
            logger.error("Claude API error: %s", exc)
            raise LLMConnectionError(
                "Anthropic API returned an error",
                model=self._config.model,
                detail=str(exc),
            ) from exc

        try:
            text: str = response.content[0].text
        except (IndexError, AttributeError) as exc:
            raise LLMResponseError(
                "Unexpected Anthropic response structure",
                model=self._config.model,
                detail=str(exc),
            ) from exc

        return text.strip()
