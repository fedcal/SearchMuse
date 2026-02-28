"""Unit tests for immutable domain models.

Verifies that all dataclasses are frozen, that with_* methods return
new instances without mutating the originals, and that model construction
exposes all expected fields.
"""

from __future__ import annotations

import dataclasses
from datetime import UTC, datetime

import pytest

from searchmuse.domain.enums import RelevanceScore, SearchPhase
from searchmuse.domain.models import (
    Citation,
    SearchIteration,
    SearchQuery,
    SearchResult,
    SearchState,
    SearchStrategy,
    Source,
)

# ---------------------------------------------------------------------------
# Immutability tests
# ---------------------------------------------------------------------------


class TestFrozenDataclasses:
    """All domain models must raise FrozenInstanceError on attribute assignment."""

    def test_search_query_is_frozen(self, sample_query: SearchQuery) -> None:
        with pytest.raises(dataclasses.FrozenInstanceError):
            sample_query.raw_text = "mutated"  # type: ignore[misc]

    def test_search_strategy_is_frozen(self, sample_strategy: SearchStrategy) -> None:
        with pytest.raises(dataclasses.FrozenInstanceError):
            sample_strategy.iteration = 99  # type: ignore[misc]

    def test_source_is_frozen(self, sample_source: Source) -> None:
        with pytest.raises(dataclasses.FrozenInstanceError):
            sample_source.url = "https://evil.example.com"  # type: ignore[misc]

    def test_citation_is_frozen(self, sample_citation: Citation) -> None:
        with pytest.raises(dataclasses.FrozenInstanceError):
            sample_citation.index = 42  # type: ignore[misc]

    def test_search_state_is_frozen(self, sample_search_state: SearchState) -> None:
        with pytest.raises(dataclasses.FrozenInstanceError):
            sample_search_state.phase = SearchPhase.COMPLETE  # type: ignore[misc]

    def test_search_iteration_is_frozen(self, sample_iteration: SearchIteration) -> None:
        with pytest.raises(dataclasses.FrozenInstanceError):
            sample_iteration.sufficient = True  # type: ignore[misc]


# ---------------------------------------------------------------------------
# SearchState with_* mutation methods
# ---------------------------------------------------------------------------


class TestSearchStateWithMethods:
    """with_* methods must return new instances and leave originals unchanged."""

    def test_with_new_iteration_returns_new_object(
        self,
        sample_search_state: SearchState,
        sample_iteration: SearchIteration,
    ) -> None:
        updated = sample_search_state.with_new_iteration(sample_iteration)

        assert updated is not sample_search_state

    def test_with_new_iteration_original_unchanged(
        self,
        sample_search_state: SearchState,
        sample_iteration: SearchIteration,
    ) -> None:
        _ = sample_search_state.with_new_iteration(sample_iteration)

        assert sample_search_state.iterations == ()

    def test_with_new_iteration_appends_correctly(
        self,
        sample_search_state: SearchState,
        sample_iteration: SearchIteration,
    ) -> None:
        updated = sample_search_state.with_new_iteration(sample_iteration)

        assert len(updated.iterations) == 1
        assert updated.iterations[0] is sample_iteration

    def test_with_new_iteration_accumulates_across_calls(
        self,
        sample_search_state: SearchState,
        sample_iteration: SearchIteration,
    ) -> None:
        first = sample_search_state.with_new_iteration(sample_iteration)
        second = first.with_new_iteration(sample_iteration)

        assert len(second.iterations) == 2
        assert len(first.iterations) == 1  # first unchanged

    def test_with_phase_returns_new_object(
        self,
        sample_search_state: SearchState,
    ) -> None:
        updated = sample_search_state.with_phase(SearchPhase.SCRAPING)

        assert updated is not sample_search_state

    def test_with_phase_sets_phase(
        self,
        sample_search_state: SearchState,
    ) -> None:
        updated = sample_search_state.with_phase(SearchPhase.SCRAPING)

        assert updated.phase == SearchPhase.SCRAPING

    def test_with_phase_original_phase_unchanged(
        self,
        sample_search_state: SearchState,
    ) -> None:
        _ = sample_search_state.with_phase(SearchPhase.SYNTHESIZING)

        assert sample_search_state.phase == SearchPhase.INITIALIZING

    def test_with_phase_preserves_other_fields(
        self,
        sample_search_state: SearchState,
    ) -> None:
        updated = sample_search_state.with_phase(SearchPhase.COMPLETE)

        assert updated.session_id == sample_search_state.session_id
        assert updated.query is sample_search_state.query

    def test_with_sources_returns_new_object(
        self,
        sample_search_state: SearchState,
        sample_source: Source,
    ) -> None:
        updated = sample_search_state.with_sources((sample_source,))

        assert updated is not sample_search_state

    def test_with_sources_original_unchanged(
        self,
        sample_search_state: SearchState,
        sample_source: Source,
    ) -> None:
        _ = sample_search_state.with_sources((sample_source,))

        assert sample_search_state.all_sources == ()

    def test_with_sources_merges_sources(
        self,
        sample_search_state: SearchState,
        sample_source: Source,
    ) -> None:
        first = sample_search_state.with_sources((sample_source,))
        second = first.with_sources((sample_source,))

        assert len(second.all_sources) == 2


# ---------------------------------------------------------------------------
# Model construction tests
# ---------------------------------------------------------------------------


class TestSourceCreation:
    """Source must expose all declared fields after construction."""

    def test_source_fields_accessible(self, sample_source: Source) -> None:
        assert sample_source.source_id
        assert sample_source.content_id
        assert sample_source.url.startswith("https://")
        assert sample_source.title
        assert sample_source.snippet
        assert sample_source.relevance_score == RelevanceScore.HIGH
        assert sample_source.credibility_notes
        assert sample_source.author is None
        assert isinstance(sample_source.accessed_at, datetime)

    def test_source_with_author(self) -> None:
        source = Source(
            source_id="abc123",
            content_id="def456",
            url="https://example.com/article",
            title="An Article",
            snippet="Short excerpt.",
            relevance_score=RelevanceScore.MEDIUM,
            credibility_notes="Unknown publication.",
            author="Jane Doe",
            accessed_at=datetime.now(UTC),
        )

        assert source.author == "Jane Doe"


class TestCitationCreation:
    """Citation must expose all declared fields after construction."""

    def test_citation_fields_accessible(self, sample_citation: Citation) -> None:
        assert sample_citation.citation_id
        assert sample_citation.source_id
        assert sample_citation.index == 1
        assert "[1]" in sample_citation.formatted_text
        assert sample_citation.url.startswith("https://")

    def test_citation_index_ordering(
        self, sample_source: Source, sample_citation: Citation
    ) -> None:
        second = Citation(
            citation_id="zz99",
            source_id=sample_source.source_id,
            index=2,
            formatted_text="[2] Another source.",
            url="https://example.com",
        )

        assert sample_citation.index < second.index


class TestSearchResultCreation:
    """SearchResult must expose all declared fields after construction."""

    def test_search_result_fields_accessible(
        self,
        sample_query: SearchQuery,
        sample_citation: Citation,
    ) -> None:
        result = SearchResult(
            session_id="sess001",
            query=sample_query,
            synthesis="Quantum entanglement is a correlation between particles...",
            citations=(sample_citation,),
            total_sources_found=5,
            iterations_performed=2,
            duration_seconds=12.34,
        )

        assert result.session_id == "sess001"
        assert result.query is sample_query
        assert "entanglement" in result.synthesis
        assert len(result.citations) == 1
        assert result.total_sources_found == 5
        assert result.iterations_performed == 2
        assert result.duration_seconds == pytest.approx(12.34)

    def test_search_result_is_frozen(
        self,
        sample_query: SearchQuery,
        sample_citation: Citation,
    ) -> None:
        result = SearchResult(
            session_id="sess002",
            query=sample_query,
            synthesis="Answer text.",
            citations=(sample_citation,),
            total_sources_found=1,
            iterations_performed=1,
            duration_seconds=3.0,
        )

        with pytest.raises(dataclasses.FrozenInstanceError):
            result.synthesis = "hacked"  # type: ignore[misc]


class TestSearchQueryNormalization:
    """SearchQuery stores both raw and normalized text independently."""

    def test_query_preserves_raw_text(self, sample_query: SearchQuery) -> None:
        assert sample_query.raw_text == "  What is quantum entanglement?  "

    def test_query_stores_normalized_text(self, sample_query: SearchQuery) -> None:
        assert sample_query.normalized_text == "What is quantum entanglement?"

    def test_query_language_field(self, sample_query: SearchQuery) -> None:
        assert sample_query.language == "en"
