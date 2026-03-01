"""Tests for searchmuse.domain.enums."""

from searchmuse.domain.enums import (
    ContentType,
    RelevanceScore,
    SearchPhase,
    SourceStatus,
)


def test_search_phase_values():
    assert SearchPhase.INITIALIZING == "initializing"
    assert SearchPhase.COMPLETE == "complete"
    assert SearchPhase.FAILED == "failed"


def test_search_phase_all_members():
    members = list(SearchPhase)
    assert len(members) == 8


def test_content_type_values():
    assert ContentType.HTML == "html"
    assert ContentType.PDF == "pdf"
    assert ContentType.PLAIN_TEXT == "plain_text"
    assert ContentType.JSON == "json"


def test_relevance_score_values():
    assert RelevanceScore.HIGH == "high"
    assert RelevanceScore.MEDIUM == "medium"
    assert RelevanceScore.LOW == "low"
    assert RelevanceScore.IRRELEVANT == "irrelevant"


def test_source_status_values():
    assert SourceStatus.PENDING == "pending"
    assert SourceStatus.CITED == "cited"
    assert SourceStatus.FAILED == "failed"


def test_enums_are_str():
    assert isinstance(SearchPhase.INITIALIZING, str)
    assert isinstance(ContentType.HTML, str)
    assert isinstance(RelevanceScore.HIGH, str)
    assert isinstance(SourceStatus.PENDING, str)
