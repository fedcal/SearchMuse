"""Pure helper functions shared by all LLM adapters.

Extracted from ``ollama_adapter`` so that every adapter implementation
can reuse formatting and validation logic without duplication.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from searchmuse.domain.enums import RelevanceScore

if TYPE_CHECKING:
    from searchmuse.domain.models import SearchIteration, Source

VALID_RELEVANCE_VALUES: frozenset[str] = frozenset(rv.value for rv in RelevanceScore)


def summarise_iteration(iteration: SearchIteration) -> str:
    """Return a one-line summary of a previous iteration for the strategy prompt."""
    terms = ", ".join(iteration.strategy.search_terms) or "(none)"
    source_count = len(iteration.sources_found)
    return (
        f"Iteration {iteration.iteration_number}: "
        f"terms=[{terms}], "
        f"sources_found={source_count}, "
        f"coverage_assessment={iteration.coverage_assessment!r}"
    )


def format_source_summary(index: int, source: Source) -> str:
    """Return a short numbered summary line for a source."""
    return f"[{index}] {source.title} ({source.url}) — relevance: {source.relevance_score}"


def format_source_detail(index: int, source: Source) -> str:
    """Return a detailed numbered block for a source suitable for synthesis."""
    return (
        f"[{index}] {source.title}\n"
        f"    URL: {source.url}\n"
        f"    Snippet: {source.snippet}"
    )
