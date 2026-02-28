"""Abstract base class for all LLM adapters.

``BaseLLMAdapter`` implements the four :class:`~searchmuse.ports.llm_port.LLMPort`
methods (strategy, relevance, coverage, synthesis) by composing prompt
formatting, a call to the abstract ``_chat`` method, and JSON parsing.

Concrete subclasses only need to implement ``__init__`` and ``_chat``.
"""

from __future__ import annotations

import json
import logging
import uuid
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from searchmuse.adapters.llm._helpers import (
    VALID_RELEVANCE_VALUES,
    format_source_detail,
    format_source_summary,
    summarise_iteration,
)
from searchmuse.adapters.llm.prompts import (
    COVERAGE_PROMPT,
    RELEVANCE_PROMPT,
    STRATEGY_PROMPT,
    SYNTHESIS_PROMPT,
)
from searchmuse.domain.enums import RelevanceScore
from searchmuse.domain.errors import LLMResponseError
from searchmuse.domain.models import SearchStrategy

if TYPE_CHECKING:
    from searchmuse.domain.models import (
        ExtractedContent,
        SearchIteration,
        SearchQuery,
        Source,
    )
    from searchmuse.infrastructure.config import LLMConfig

logger: logging.Logger = logging.getLogger(__name__)


class BaseLLMAdapter(ABC):
    """Abstract base class shared by every LLM adapter.

    Subclasses **must** override:
      - ``__init__``  — set up provider-specific clients.
      - ``_chat``     — send a prompt and return the raw response text.

    All four public ``LLMPort`` methods are implemented here in terms
    of ``_chat`` and ``_parse_json``.
    """

    def __init__(self, config: LLMConfig) -> None:
        self._config: LLMConfig = config

    # ------------------------------------------------------------------
    # Abstract
    # ------------------------------------------------------------------

    @abstractmethod
    async def _chat(self, prompt: str, *, temperature: float) -> str:
        """Send a single-turn chat request and return the stripped response text.

        Subclasses must translate provider-specific connection errors into
        :class:`~searchmuse.domain.errors.LLMConnectionError`.
        """

    # ------------------------------------------------------------------
    # Public interface (LLMPort)
    # ------------------------------------------------------------------

    async def generate_search_strategy(
        self,
        query: SearchQuery,
        previous_iterations: tuple[SearchIteration, ...],
    ) -> SearchStrategy:
        """Generate a search strategy for the next iteration."""
        previous_summaries = (
            "\n".join(summarise_iteration(it) for it in previous_iterations)
            if previous_iterations
            else "(none — this is the first iteration)"
        )

        prompt = STRATEGY_PROMPT.format(
            query=query.normalized_text,
            previous_summaries=previous_summaries,
        )

        logger.info(
            "Generating search strategy: query_id=%r iteration=%d",
            query.query_id,
            len(previous_iterations) + 1,
        )

        raw_text = await self._chat(prompt, temperature=self._config.strategy_temperature)
        data = self._parse_json(
            raw_text,
            required_keys={"search_terms", "target_domains", "reasoning"},
        )

        search_terms: tuple[str, ...] = tuple(
            str(t) for t in data.get("search_terms", []) if str(t).strip()
        )
        target_domains: tuple[str, ...] = tuple(
            str(d) for d in data.get("target_domains", []) if str(d).strip()
        )
        reasoning: str = str(data.get("reasoning", "")).strip()

        strategy = SearchStrategy(
            strategy_id=str(uuid.uuid4()),
            query_id=query.query_id,
            search_terms=search_terms,
            target_domains=target_domains,
            reasoning=reasoning,
            iteration=len(previous_iterations) + 1,
        )

        logger.debug(
            "Strategy generated: strategy_id=%r terms=%r",
            strategy.strategy_id,
            strategy.search_terms,
        )
        return strategy

    async def assess_content_relevance(
        self,
        content: ExtractedContent,
        query: SearchQuery,
    ) -> RelevanceScore:
        """Assess how relevant extracted content is to the query."""
        prompt = RELEVANCE_PROMPT.format(
            query=query.normalized_text,
            title=content.title,
            url=content.url,
            content_text=content.clean_text[:8000],
        )

        logger.info(
            "Assessing relevance: content_id=%r url=%r",
            content.content_id,
            content.url,
        )

        raw_text = await self._chat(prompt, temperature=self._config.assessment_temperature)
        data = self._parse_json(raw_text, required_keys={"relevance"})

        raw_value: str = str(data.get("relevance", "")).strip().lower()
        if raw_value not in VALID_RELEVANCE_VALUES:
            raise LLMResponseError(
                "Unrecognised relevance value in LLM response",
                model=self._config.model,
                detail=f"Got {raw_value!r}; expected one of {sorted(VALID_RELEVANCE_VALUES)}",
            )

        score = RelevanceScore(raw_value)
        logger.debug("Relevance assessed: content_id=%r score=%r", content.content_id, score)
        return score

    async def assess_coverage(
        self,
        query: SearchQuery,
        sources: tuple[Source, ...],
    ) -> tuple[float, str]:
        """Evaluate how well the accumulated sources cover the query."""
        source_summaries = "\n".join(
            format_source_summary(i + 1, src) for i, src in enumerate(sources)
        ) or "(no sources collected yet)"

        prompt = COVERAGE_PROMPT.format(
            query=query.normalized_text,
            source_count=len(sources),
            source_summaries=source_summaries,
        )

        logger.info(
            "Assessing coverage: query_id=%r source_count=%d",
            query.query_id,
            len(sources),
        )

        raw_text = await self._chat(prompt, temperature=self._config.assessment_temperature)
        data = self._parse_json(raw_text, required_keys={"coverage_score", "assessment"})

        try:
            raw_score = float(data["coverage_score"])
        except (TypeError, ValueError) as exc:
            raise LLMResponseError(
                "coverage_score is not a valid float",
                model=self._config.model,
                detail=str(exc),
            ) from exc

        coverage_score = max(0.0, min(1.0, raw_score))
        assessment: str = str(data.get("assessment", "")).strip()

        logger.debug(
            "Coverage assessed: query_id=%r score=%.2f",
            query.query_id,
            coverage_score,
        )
        return coverage_score, assessment

    async def synthesize_answer(
        self,
        query: SearchQuery,
        sources: tuple[Source, ...],
    ) -> str:
        """Synthesize a final answer from the collected sources."""
        source_details = "\n\n".join(
            format_source_detail(i + 1, src) for i, src in enumerate(sources)
        ) or "(no sources available)"

        prompt = SYNTHESIS_PROMPT.format(
            query=query.normalized_text,
            source_count=len(sources),
            source_details=source_details,
        )

        logger.info(
            "Synthesising answer: query_id=%r source_count=%d",
            query.query_id,
            len(sources),
        )

        answer = await self._chat(prompt, temperature=self._config.synthesis_temperature)

        if not answer.strip():
            raise LLMResponseError(
                "Model returned an empty synthesis",
                model=self._config.model,
                detail="Empty response body after stripping whitespace",
            )

        logger.debug("Answer synthesised: query_id=%r chars=%d", query.query_id, len(answer))
        return answer.strip()

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------

    def _parse_json(self, raw: str, *, required_keys: set[str]) -> dict[str, Any]:
        """Parse a JSON string and validate that required keys are present."""
        try:
            data: Any = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise LLMResponseError(
                "LLM response is not valid JSON",
                model=self._config.model,
                detail=f"JSONDecodeError at position {exc.pos}: {exc.msg}\nRaw: {raw[:500]!r}",
            ) from exc

        if not isinstance(data, dict):
            raise LLMResponseError(
                "LLM response JSON is not an object",
                model=self._config.model,
                detail=f"Got type {type(data).__name__!r}; raw={raw[:500]!r}",
            )

        missing = required_keys - data.keys()
        if missing:
            raise LLMResponseError(
                "LLM response JSON missing required keys",
                model=self._config.model,
                detail=f"Missing keys: {sorted(missing)}; raw={raw[:500]!r}",
            )

        return data
