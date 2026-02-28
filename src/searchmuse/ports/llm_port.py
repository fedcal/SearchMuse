"""Protocol definition for LLM adapter port."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from searchmuse.domain.enums import RelevanceScore
    from searchmuse.domain.models import (
        ExtractedContent,
        SearchIteration,
        SearchQuery,
        SearchStrategy,
        Source,
    )


@runtime_checkable
class LLMPort(Protocol):
    """Abstract port for interacting with a language model backend.

    Implementations must be async-safe and stateless across calls.
    All methods raise LLMError subclasses on failure.
    """

    async def generate_search_strategy(
        self,
        query: SearchQuery,
        previous_iterations: tuple[SearchIteration, ...],
    ) -> SearchStrategy:
        """Generate a search strategy for the next iteration.

        Args:
            query: The current search query.
            previous_iterations: All iterations completed so far,
                used to avoid repeating ineffective strategies.

        Returns:
            A new frozen SearchStrategy with search terms and reasoning.
        """
        ...

    async def assess_content_relevance(
        self,
        content: ExtractedContent,
        query: SearchQuery,
    ) -> RelevanceScore:
        """Assess how relevant extracted content is to the query.

        Args:
            content: Extracted and cleaned page content.
            query: The search query to assess against.

        Returns:
            A RelevanceScore enum value.
        """
        ...

    async def assess_coverage(
        self,
        query: SearchQuery,
        sources: tuple[Source, ...],
    ) -> tuple[float, str]:
        """Evaluate how well the accumulated sources cover the query.

        Args:
            query: The search query being answered.
            sources: All relevant sources collected so far.

        Returns:
            A tuple of (coverage_score, narrative_assessment) where
            coverage_score is in [0.0, 1.0] and narrative_assessment
            describes remaining gaps.
        """
        ...

    async def synthesize_answer(
        self,
        query: SearchQuery,
        sources: tuple[Source, ...],
    ) -> str:
        """Synthesize a final answer from the collected sources.

        Args:
            query: The original search query.
            sources: All relevant sources to draw from.

        Returns:
            A comprehensive answer string with inline citation markers.
        """
        ...
