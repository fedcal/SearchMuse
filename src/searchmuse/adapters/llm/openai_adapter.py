"""OpenAI LLM adapter implementing the LLMPort protocol.

Uses the ``openai`` async client.  The SDK is imported lazily so that
the package is only required when the user selects ``provider: openai``.

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


class OpenAILLMAdapter(BaseLLMAdapter):
    """Concrete LLM adapter backed by the OpenAI Chat Completions API."""

    def __init__(self, config: LLMConfig, *, api_key: str) -> None:
        super().__init__(config)
        try:
            import openai
        except ImportError as exc:
            raise ImportError(
                "The 'openai' package is required for the OpenAI provider. "
                "Install it with: pip install 'searchmuse[openai]'"
            ) from exc

        self._sdk: Any = openai
        self._client = openai.AsyncOpenAI(
            api_key=api_key,
            max_retries=0,
            timeout=config.timeout,
        )
        logger.debug(
            "OpenAILLMAdapter initialised: model=%r",
            config.model,
        )

    async def _chat(self, prompt: str, *, temperature: float) -> str:
        """Send a single-turn chat completion request to the OpenAI API."""
        sdk = self._sdk

        try:
            response = await self._client.chat.completions.create(
                model=self._config.model,
                max_tokens=self._config.max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}],
            )
        except sdk.AuthenticationError as exc:
            raise LLMAuthenticationError(
                "OpenAI API key is invalid or expired",
                model=self._config.model,
                detail=str(exc),
            ) from exc
        except (sdk.APIConnectionError, sdk.APITimeoutError) as exc:
            logger.error("OpenAI connection error: %s", exc)
            raise LLMConnectionError(
                "Failed to connect to OpenAI API",
                model=self._config.model,
                detail=str(exc),
            ) from exc
        except sdk.APIStatusError as exc:
            logger.error("OpenAI API error: %s", exc)
            raise LLMConnectionError(
                "OpenAI API returned an error",
                model=self._config.model,
                detail=str(exc),
            ) from exc

        try:
            choice = response.choices[0]
            text: str = choice.message.content or ""
        except (IndexError, AttributeError) as exc:
            raise LLMResponseError(
                "Unexpected OpenAI response structure",
                model=self._config.model,
                detail=str(exc),
            ) from exc

        return text.strip()
