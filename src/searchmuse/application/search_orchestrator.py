"""Search orchestrator: iterative search engine driving the full pipeline.

Coordinates the search loop: strategy -> search -> scrape -> extract ->
assess -> coverage check -> synthesize. All state is immutable; each step
returns a new SearchState snapshot.
"""

from __future__ import annotations

import logging
import time
from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from searchmuse.application.progress import NullProgress, ProgressEvent
from searchmuse.domain.enums import RelevanceScore, SearchPhase
from searchmuse.domain.models import (
    Citation,
    SearchIteration,
    SearchQuery,
    SearchResult,
    SearchState,
    Source,
)
from searchmuse.domain.validators import validate_query
from searchmuse.infrastructure.i18n import t

if TYPE_CHECKING:
    from searchmuse.application.progress import ProgressCallback
    from searchmuse.infrastructure.config import SearchMuseConfig
    from searchmuse.ports.content_extractor_port import ContentExtractorPort
    from searchmuse.ports.llm_port import LLMPort
    from searchmuse.ports.scraper_port import ScraperPort
    from searchmuse.ports.search_port import SearchPort
    from searchmuse.ports.source_repository_port import SourceRepositoryPort

logger = logging.getLogger(__name__)


def _short_id() -> str:
    """Return an 8-character hex identifier."""
    return uuid4().hex[:8]


def _now() -> datetime:
    """Return the current UTC datetime."""
    return datetime.now(UTC)


class SearchOrchestrator:
    """Drives the iterative search pipeline.

    Accepts port implementations via constructor injection and coordinates
    the full search lifecycle from query to synthesized answer.
    """

    def __init__(
        self,
        *,
        config: SearchMuseConfig,
        llm: LLMPort,
        search: SearchPort,
        scraper: ScraperPort,
        extractor: ContentExtractorPort,
        repository: SourceRepositoryPort,
        progress: ProgressCallback | None = None,
    ) -> None:
        self._config = config
        self._llm = llm
        self._search = search
        self._scraper = scraper
        self._extractor = extractor
        self._repository = repository
        self._progress: ProgressCallback = progress or NullProgress()

    def _emit(
        self,
        phase: SearchPhase,
        message: str,
        iteration: int = 0,
        detail: str = "",
    ) -> None:
        """Emit a progress event."""
        self._progress(ProgressEvent(
            phase=phase,
            message=message,
            iteration=iteration,
            detail=detail,
        ))

    async def run(
        self,
        raw_query: str,
        chat_context: tuple[tuple[str, str], ...] = (),
    ) -> SearchResult:
        """Execute a full iterative search and return the final result.

        Args:
            raw_query: The raw user query text.
            chat_context: Optional pairs of (query_text, synthesis_text)
                from previous conversations in the same chat session.

        Returns:
            A frozen SearchResult with synthesis and citations.
        """
        start_time = time.monotonic()

        normalized = validate_query(raw_query)
        query = SearchQuery(
            query_id=_short_id(),
            raw_text=raw_query,
            normalized_text=normalized,
            language=self._config.search.default_language,
            created_at=_now(),
        )

        state = SearchState(
            session_id=_short_id(),
            query=query,
            iterations=(),
            all_sources=(),
            phase=SearchPhase.INITIALIZING,
        )

        self._emit(SearchPhase.INITIALIZING, t("search_started"))

        max_iter = self._config.search.max_iterations
        min_sources = self._config.search.min_sources
        min_coverage = self._config.search.min_coverage_score

        for iteration_num in range(1, max_iter + 1):
            state = await self._run_iteration(
                state=state,
                iteration_num=iteration_num,
                chat_context=chat_context,
            )

            latest = state.iterations[-1]
            sources_count = len(state.all_sources)

            if latest.sufficient and sources_count >= min_sources:
                logger.info(
                    "Coverage sufficient at iteration %d (sources=%d)",
                    iteration_num,
                    sources_count,
                )
                break

            coverage_score = self._parse_coverage_score(latest.coverage_assessment)
            if coverage_score >= min_coverage and sources_count >= min_sources:
                logger.info(
                    "Coverage score %.2f >= %.2f at iteration %d",
                    coverage_score,
                    min_coverage,
                    iteration_num,
                )
                break

        result = await self._synthesize(state, start_time)
        return result

    async def _run_iteration(
        self,
        *,
        state: SearchState,
        iteration_num: int,
        chat_context: tuple[tuple[str, str], ...] = (),
    ) -> SearchState:
        """Run a single search iteration and return updated state."""
        state = state.with_phase(SearchPhase.STRATEGIZING)
        self._emit(
            SearchPhase.STRATEGIZING,
            t("generating_strategy"),
            iteration=iteration_num,
        )

        strategy = await self._llm.generate_search_strategy(
            state.query, state.iterations, chat_context,
        )

        state = state.with_phase(SearchPhase.SCRAPING)
        self._emit(
            SearchPhase.SCRAPING,
            ", ".join(strategy.search_terms[:3]),
            iteration=iteration_num,
        )

        all_urls: list[str] = []
        for term in strategy.search_terms:
            hits = await self._search.search(
                term,
                max_results=self._config.search.results_per_query,
            )
            all_urls.extend(hit.url for hit in hits)

        unique_urls = tuple(dict.fromkeys(all_urls))
        already_scraped = {
            src.url for src in state.all_sources
        }
        urls_to_scrape = tuple(
            url for url in unique_urls if url not in already_scraped
        )

        pages = await self._scraper.scrape_many(urls_to_scrape)
        pages_scraped = len(pages)

        self._emit(
            SearchPhase.SCRAPING,
            t("scraping_pages", count=pages_scraped),
            iteration=iteration_num,
        )

        state = state.with_phase(SearchPhase.EXTRACTING)
        self._emit(
            SearchPhase.EXTRACTING,
            t("extracting_content"),
            iteration=iteration_num,
        )

        extracted = []
        for page in pages:
            try:
                content = self._extractor.extract(page)
                extracted.append(content)
            except Exception:
                logger.debug("Extraction failed for %s", page.url)

        contents_extracted = len(extracted)

        state = state.with_phase(SearchPhase.ASSESSING)
        self._emit(
            SearchPhase.ASSESSING,
            t("assessing_contents", count=contents_extracted),
            iteration=iteration_num,
        )

        new_sources: list[Source] = []
        for content in extracted:
            try:
                relevance = await self._llm.assess_content_relevance(
                    content, state.query,
                )
            except Exception:
                logger.debug("Relevance assessment failed for %s", content.url)
                continue

            if relevance in (RelevanceScore.HIGH, RelevanceScore.MEDIUM):
                source = Source(
                    source_id=_short_id(),
                    content_id=content.content_id,
                    url=content.url,
                    title=content.title,
                    snippet=content.clean_text[:200],
                    relevance_score=relevance,
                    credibility_notes="",
                    author=content.author,
                    accessed_at=_now(),
                )
                new_sources.append(source)

                await self._repository.save(source)

        state = state.with_sources(tuple(new_sources))

        coverage_score, coverage_text = await self._llm.assess_coverage(
            state.query, state.all_sources,
        )

        sufficient = (
            coverage_score >= self._config.search.min_coverage_score
            and len(state.all_sources) >= self._config.search.min_sources
        )

        iteration = SearchIteration(
            iteration_number=iteration_num,
            strategy=strategy,
            pages_scraped=pages_scraped,
            contents_extracted=contents_extracted,
            sources_found=tuple(new_sources),
            coverage_assessment=f"{coverage_score:.2f}|{coverage_text}",
            sufficient=sufficient,
        )

        state = state.with_new_iteration(iteration)

        self._emit(
            SearchPhase.ASSESSING,
            f"Iteration {iteration_num}: {len(new_sources)} new sources, "
            f"coverage {coverage_score:.0%}",
            iteration=iteration_num,
        )

        return state

    async def _synthesize(
        self,
        state: SearchState,
        start_time: float,
    ) -> SearchResult:
        """Synthesize the final answer from accumulated sources."""
        state = state.with_phase(SearchPhase.SYNTHESIZING)
        self._emit(SearchPhase.SYNTHESIZING, t("synthesizing"))

        synthesis = await self._llm.synthesize_answer(
            state.query, state.all_sources,
        )

        include_snippets = self._config.output.include_snippets
        max_snippet_len = self._config.output.max_snippet_length

        citations = tuple(
            Citation(
                citation_id=_short_id(),
                source_id=source.source_id,
                index=idx,
                formatted_text=(
                    f"[{idx}] {source.title}. {source.url}"
                ),
                url=source.url,
                snippet=(
                    source.snippet[:max_snippet_len]
                    if include_snippets else ""
                ),
            )
            for idx, source in enumerate(state.all_sources, start=1)
        )

        duration = time.monotonic() - start_time

        state = state.with_phase(SearchPhase.COMPLETE)
        self._emit(SearchPhase.COMPLETE, t("search_complete", duration=f"{duration:.1f}"))

        return SearchResult(
            session_id=state.session_id,
            query=state.query,
            synthesis=synthesis,
            citations=citations,
            total_sources_found=len(state.all_sources),
            iterations_performed=len(state.iterations),
            duration_seconds=round(duration, 2),
        )

    @staticmethod
    def _parse_coverage_score(assessment: str) -> float:
        """Extract coverage score from assessment string 'score|text'."""
        try:
            score_str = assessment.split("|", 1)[0]
            return float(score_str)
        except (ValueError, IndexError):
            return 0.0
