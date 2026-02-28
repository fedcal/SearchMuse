"""Ollama LLM adapter implementing the LLMPort protocol.

Uses the official ``ollama`` Python package (AsyncClient) to communicate with a
locally running Ollama server.  Inherits shared prompt logic from
:class:`~searchmuse.adapters.llm._base.BaseLLMAdapter`.

Error handling contract:
  - LLMConnectionError: raised when the Ollama server cannot be reached.
  - LLMResponseError:   raised when a response cannot be parsed as expected JSON.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import ollama

from searchmuse.adapters.llm._base import BaseLLMAdapter
from searchmuse.domain.errors import LLMConnectionError, LLMResponseError

if TYPE_CHECKING:
    from searchmuse.infrastructure.config import LLMConfig

logger: logging.Logger = logging.getLogger(__name__)


class OllamaLLMAdapter(BaseLLMAdapter):
    """Concrete LLM adapter backed by a locally running Ollama server.

    Implements the LLMPort protocol via :class:`BaseLLMAdapter`.
    Only ``__init__`` and ``_chat`` are provider-specific.
    """

    def __init__(self, config: LLMConfig) -> None:
        super().__init__(config)
        self._client: ollama.AsyncClient = ollama.AsyncClient(host=config.base_url)
        logger.debug(
            "OllamaLLMAdapter initialised: model=%r base_url=%r",
            config.model,
            config.base_url,
        )

    async def _chat(self, prompt: str, *, temperature: float) -> str:
        """Send a single-turn chat request to Ollama and return the response text."""
        options: dict[str, Any] = {
            "temperature": temperature,
            "num_predict": self._config.max_tokens,
        }
        messages = [{"role": "user", "content": prompt}]

        try:
            response = await self._client.chat(
                model=self._config.model,
                messages=messages,
                options=options,
            )
        except (ConnectionError, TimeoutError) as exc:
            logger.error("Ollama connection error: %s", exc)
            raise LLMConnectionError(
                "Failed to connect to Ollama server",
                model=self._config.model,
                detail=str(exc),
            ) from exc
        except Exception as exc:
            logger.error("Unexpected Ollama error: %s", exc)
            raise LLMConnectionError(
                "Unexpected error communicating with Ollama",
                model=self._config.model,
                detail=str(exc),
            ) from exc

        try:
            text: str = response.message.content or ""
        except AttributeError as exc:
            raise LLMResponseError(
                "Unexpected Ollama response structure",
                model=self._config.model,
                detail=str(exc),
            ) from exc

        return text.strip()
