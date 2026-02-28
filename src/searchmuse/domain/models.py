"""Immutable domain models for SearchMuse.

All dataclasses are frozen and use slots for memory efficiency.
State mutations always return new instances via dataclasses.replace().
"""

from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime

    from searchmuse.domain.enums import ContentType, RelevanceScore, SearchPhase


@dataclasses.dataclass(frozen=True, slots=True)
class SearchHit:
    """A raw search engine result before scraping.

    Attributes:
        url: The URL returned by the search engine.
        title: The result title/headline.
        snippet: Short description from the search engine.
    """

    url: str
    title: str
    snippet: str


@dataclasses.dataclass(frozen=True, slots=True)
class SearchQuery:
    """Represents a normalised user search query.

    Attributes:
        query_id: Unique identifier for this query.
        raw_text: The original unmodified query text.
        normalized_text: Stripped and validated query text.
        language: BCP-47 language code (e.g. "en").
        created_at: UTC timestamp of query creation.
    """

    query_id: str
    raw_text: str
    normalized_text: str
    language: str
    created_at: datetime


@dataclasses.dataclass(frozen=True, slots=True)
class SearchStrategy:
    """LLM-generated strategy for a single search iteration.

    Attributes:
        strategy_id: Unique identifier for this strategy.
        query_id: ID of the parent query.
        search_terms: Ordered collection of search terms to use.
        target_domains: Optional domain restrictions for search.
        reasoning: LLM explanation of why this strategy was chosen.
        iteration: The iteration number this strategy belongs to.
    """

    strategy_id: str
    query_id: str
    search_terms: tuple[str, ...]
    target_domains: tuple[str, ...]
    reasoning: str
    iteration: int


@dataclasses.dataclass(frozen=True, slots=True)
class ScrapedPage:
    """Raw HTTP response from a single scraped URL.

    Attributes:
        page_id: Unique identifier for this scraped page.
        url: The URL that was requested.
        raw_html: Full raw HTML body as a string.
        http_status: HTTP response status code.
        content_type: Detected content type of the response.
        scraped_at: UTC timestamp when the page was fetched.
        scraper_used: Identifier of the scraper adapter used.
    """

    page_id: str
    url: str
    raw_html: str
    http_status: int
    content_type: ContentType
    scraped_at: datetime
    scraper_used: str


@dataclasses.dataclass(frozen=True, slots=True)
class ExtractedContent:
    """Clean textual content extracted from a scraped page.

    Attributes:
        content_id: Unique identifier for this extracted content.
        page_id: ID of the parent scraped page.
        url: Source URL for reference.
        title: Extracted page title.
        clean_text: Main body text after noise removal.
        author: Detected author name, if available.
        published_date: Detected publication date string, if available.
        word_count: Number of words in clean_text.
    """

    content_id: str
    page_id: str
    url: str
    title: str
    clean_text: str
    author: str | None
    published_date: str | None
    word_count: int


@dataclasses.dataclass(frozen=True, slots=True)
class Source:
    """An assessed source deemed relevant to the search query.

    Attributes:
        source_id: Unique identifier for this source.
        content_id: ID of the parent extracted content.
        url: Source URL.
        title: Page title used for display.
        snippet: Short excerpt illustrating relevance.
        relevance_score: LLM-assigned relevance category.
        credibility_notes: LLM assessment of source credibility.
        author: Author name if detected.
        accessed_at: UTC timestamp when the source was accessed.
    """

    source_id: str
    content_id: str
    url: str
    title: str
    snippet: str
    relevance_score: RelevanceScore
    credibility_notes: str
    author: str | None
    accessed_at: datetime


@dataclasses.dataclass(frozen=True, slots=True)
class Citation:
    """A formatted citation derived from a source.

    Attributes:
        citation_id: Unique identifier for this citation.
        source_id: ID of the parent source.
        index: 1-based display index in the final report.
        formatted_text: Human-readable citation string.
        url: URL included in the citation.
    """

    citation_id: str
    source_id: str
    index: int
    formatted_text: str
    url: str


@dataclasses.dataclass(frozen=True, slots=True)
class SearchIteration:
    """Snapshot of a single completed search iteration.

    Attributes:
        iteration_number: 1-based sequence number.
        strategy: The strategy used for this iteration.
        pages_scraped: Count of pages fetched.
        contents_extracted: Count of pages successfully extracted.
        sources_found: Sources deemed relevant in this iteration.
        coverage_assessment: LLM narrative on remaining coverage gaps.
        sufficient: True when the LLM considers coverage adequate.
    """

    iteration_number: int
    strategy: SearchStrategy
    pages_scraped: int
    contents_extracted: int
    sources_found: tuple[Source, ...]
    coverage_assessment: str
    sufficient: bool


@dataclasses.dataclass(frozen=True, slots=True)
class SearchState:
    """Immutable snapshot of a running search session.

    All mutations return a new SearchState via dataclasses.replace().

    Attributes:
        session_id: Unique identifier for this search session.
        query: The validated search query.
        iterations: Ordered record of completed iterations.
        all_sources: Accumulated sources across all iterations.
        phase: Current phase in the search lifecycle.
    """

    session_id: str
    query: SearchQuery
    iterations: tuple[SearchIteration, ...]
    all_sources: tuple[Source, ...]
    phase: SearchPhase

    def with_new_iteration(self, iteration: SearchIteration) -> SearchState:
        """Return a new state with the given iteration appended.

        Args:
            iteration: The completed iteration to record.

        Returns:
            A new SearchState with the iteration added to iterations.
        """
        return dataclasses.replace(
            self,
            iterations=(*self.iterations, iteration),
        )

    def with_phase(self, phase: SearchPhase) -> SearchState:
        """Return a new state with the phase updated.

        Args:
            phase: The new search phase.

        Returns:
            A new SearchState with the updated phase.
        """
        return dataclasses.replace(self, phase=phase)

    def with_sources(self, new_sources: tuple[Source, ...]) -> SearchState:
        """Return a new state with additional sources merged in.

        Args:
            new_sources: Sources discovered in the latest iteration.

        Returns:
            A new SearchState with new_sources appended to all_sources.
        """
        return dataclasses.replace(
            self,
            all_sources=(*self.all_sources, *new_sources),
        )


@dataclasses.dataclass(frozen=True, slots=True)
class SearchResult:
    """Final output produced after a completed search session.

    Attributes:
        session_id: Identifier of the originating search session.
        query: The search query that was answered.
        synthesis: LLM-generated answer narrative.
        citations: Ordered citations referenced in the synthesis.
        total_sources_found: Total number of relevant sources assessed.
        iterations_performed: Number of search iterations executed.
        duration_seconds: Wall-clock time from start to completion.
    """

    session_id: str
    query: SearchQuery
    synthesis: str
    citations: tuple[Citation, ...]
    total_sources_found: int
    iterations_performed: int
    duration_seconds: float
