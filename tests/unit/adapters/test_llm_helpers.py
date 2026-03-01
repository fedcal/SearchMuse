"""Tests for searchmuse.adapters.llm._helpers."""

from searchmuse.adapters.llm._helpers import (
    VALID_RELEVANCE_VALUES,
    format_source_detail,
    format_source_summary,
    summarise_iteration,
)


def test_valid_relevance_values():
    assert "high" in VALID_RELEVANCE_VALUES
    assert "medium" in VALID_RELEVANCE_VALUES
    assert "low" in VALID_RELEVANCE_VALUES
    assert "irrelevant" in VALID_RELEVANCE_VALUES
    assert len(VALID_RELEVANCE_VALUES) == 4


def test_summarise_iteration(sample_iteration):
    summary = summarise_iteration(sample_iteration)
    assert "Iteration 1" in summary
    assert "quantum entanglement" in summary
    assert "sources_found=1" in summary


def test_format_source_summary(sample_source):
    line = format_source_summary(1, sample_source)
    assert "[1]" in line
    assert sample_source.title in line
    assert sample_source.url in line


def test_format_source_detail(sample_source):
    detail = format_source_detail(1, sample_source)
    assert "[1]" in detail
    assert "URL:" in detail
    assert "Snippet:" in detail
    assert sample_source.title in detail
