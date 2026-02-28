"""Google Gemini LLM adapter implementing the LLMPort protocol.

Uses the ``google-genai`` async client.  The SDK is imported lazily so that
the package is only required when the user selects ``provider: gemini``.

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


class GeminiLLMAdapter(BaseLLMAdapter):
    """Concrete LLM adapter backed by the Google Generative AI (Gemini) API."""

    def __init__(self, config: LLMConfig, *, api_key: str) -> None:
        super().__init__(config)
        try:
            from google import genai
            from google.genai import types as genai_types
        except ImportError as exc:
            raise ImportError(
                "The 'google-genai' package is required for the Gemini provider. "
                "Install it with: pip install 'searchmuse[gemini]'"
            ) from exc

        self._genai: Any = genai
        self._genai_types: Any = genai_types
        self._client = genai.Client(api_key=api_key)
        logger.debug(
            "GeminiLLMAdapter initialised: model=%r",
            config.model,
        )

    async def _chat(self, prompt: str, *, temperature: float) -> str:
        """Send a content generation request to the Gemini API."""
        genai = self._genai
        genai_types = self._genai_types

        config = genai_types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=self._config.max_tokens,
        )

        try:
            response = await self._client.aio.models.generate_content(
                model=self._config.model,
                contents=prompt,
                config=config,
            )
        except genai.errors.ClientError as exc:
            error_str = str(exc).lower()
            if "api_key" in error_str or "401" in error_str or "403" in error_str:
                raise LLMAuthenticationError(
                    "Google API key is invalid or expired",
                    model=self._config.model,
                    detail=str(exc),
                ) from exc
            logger.error("Gemini client error: %s", exc)
            raise LLMConnectionError(
                "Gemini API returned a client error",
                model=self._config.model,
                detail=str(exc),
            ) from exc
        except Exception as exc:
            logger.error("Gemini unexpected error: %s", exc)
            raise LLMConnectionError(
                "Failed to connect to Gemini API",
                model=self._config.model,
                detail=str(exc),
            ) from exc

        try:
            text: str = response.text or ""
        except (AttributeError, ValueError) as exc:
            raise LLMResponseError(
                "Unexpected Gemini response structure",
                model=self._config.model,
                detail=str(exc),
            ) from exc

        return text.strip()
