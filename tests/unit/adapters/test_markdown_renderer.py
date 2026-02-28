"""Unit tests for MarkdownRendererAdapter.

Tests cover:
- format_name property returns the string "markdown"
- render() output contains the required ## Answer and ## Sources sections
- Citations are numbered and include both formatted_text and url
- Empty citations produce the fallback "No sources were cited." message
- Footer statistics line contains sources, iterations, and duration
- Duration is formatted to two decimal places
- Section order matches the documented layout
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from searchmuse.adapters.renderers.markdown_renderer import MarkdownRendererAdapter
from searchmuse.domain.models import Citation, SearchQuery, SearchResult

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _short_id() -> str:
    return uuid4().hex[:8]


def _make_citation(*, index: int, text: str, url: str) -> Citation:
    """Construct a minimal frozen Citation."""
    return Citation(
        citation_id=_short_id(),
        source_id=_short_id(),
        index=index,
        formatted_text=text,
        url=url,
    )


def _make_query(normalized_text: str = "What is quantum computing?") -> SearchQuery:
    """Construct a minimal frozen SearchQuery."""
    return SearchQuery(
        query_id=_short_id(),
        raw_text=normalized_text,
        normalized_text=normalized_text,
        language="en",
        created_at=datetime.now(UTC),
    )


def _make_result(
    *,
    synthesis: str = "Quantum computing leverages superposition.",
    citations: tuple[Citation, ...] = (),
    total_sources_found: int = 3,
    iterations_performed: int = 2,
    duration_seconds: float = 1.50,
) -> SearchResult:
    """Construct a minimal frozen SearchResult."""
    return SearchResult(
        session_id=_short_id(),
        query=_make_query(),
        synthesis=synthesis,
        citations=citations,
        total_sources_found=total_sources_found,
        iterations_performed=iterations_performed,
        duration_seconds=duration_seconds,
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def renderer() -> MarkdownRendererAdapter:
    """Return a default MarkdownRendererAdapter instance."""
    return MarkdownRendererAdapter()


@pytest.fixture()
def single_citation() -> Citation:
    """A single Citation for use in render tests."""
    return _make_citation(
        index=1,
        text="Quantum Computing — IBM Research",
        url="https://research.ibm.com/quantum",
    )


@pytest.fixture()
def two_citations() -> tuple[Citation, ...]:
    """Two ordered Citations for use in render tests."""
    return (
        _make_citation(
            index=1,
            text="Quantum Computing — IBM Research",
            url="https://research.ibm.com/quantum",
        ),
        _make_citation(
            index=2,
            text="Introduction to Quantum Mechanics — MIT OpenCourseWare",
            url="https://ocw.mit.edu/quantum",
        ),
    )


# ---------------------------------------------------------------------------
# format_name property
# ---------------------------------------------------------------------------


class TestFormatName:
    """Tests for the format_name property."""

    def test_format_name_is_markdown(self, renderer: MarkdownRendererAdapter) -> None:
        """format_name must return the literal string 'markdown'."""
        assert renderer.format_name == "markdown"

    def test_format_name_is_string(self, renderer: MarkdownRendererAdapter) -> None:
        """format_name must be a plain str, not an enum or other type."""
        assert isinstance(renderer.format_name, str)


# ---------------------------------------------------------------------------
# Section presence tests
# ---------------------------------------------------------------------------


class TestRenderSections:
    """Tests that the required Markdown sections are present in the output."""

    def test_render_contains_answer_section(
        self, renderer: MarkdownRendererAdapter
    ) -> None:
        """Output must contain the '## Answer' heading."""
        result = _make_result()
        output = renderer.render(result)
        assert "## Answer" in output

    def test_render_contains_sources_section(
        self, renderer: MarkdownRendererAdapter
    ) -> None:
        """Output must contain the '## Sources' heading."""
        result = _make_result()
        output = renderer.render(result)
        assert "## Sources" in output

    def test_render_contains_separator(
        self, renderer: MarkdownRendererAdapter
    ) -> None:
        """Output must contain the '---' horizontal rule separator."""
        result = _make_result()
        output = renderer.render(result)
        assert "---" in output

    def test_answer_section_appears_before_sources_section(
        self, renderer: MarkdownRendererAdapter
    ) -> None:
        """## Answer must appear earlier in the document than ## Sources."""
        result = _make_result()
        output = renderer.render(result)
        answer_pos = output.index("## Answer")
        sources_pos = output.index("## Sources")
        assert answer_pos < sources_pos

    def test_sources_section_appears_before_separator(
        self, renderer: MarkdownRendererAdapter
    ) -> None:
        """## Sources must appear before the --- separator."""
        result = _make_result()
        output = renderer.render(result)
        sources_pos = output.index("## Sources")
        separator_pos = output.index("---")
        assert sources_pos < separator_pos

    def test_synthesis_text_present_in_output(
        self, renderer: MarkdownRendererAdapter
    ) -> None:
        """The synthesis narrative must appear verbatim in the rendered output."""
        synthesis = "Unique synthesis narrative for this test."
        result = _make_result(synthesis=synthesis)
        output = renderer.render(result)
        assert synthesis in output


# ---------------------------------------------------------------------------
# Citation rendering tests
# ---------------------------------------------------------------------------


class TestRenderCitations:
    """Tests for numbered citation rendering within the ## Sources block."""

    def test_single_citation_appears_in_output(
        self,
        renderer: MarkdownRendererAdapter,
        single_citation: Citation,
    ) -> None:
        """A single citation's formatted_text must appear in the output."""
        result = _make_result(citations=(single_citation,))
        output = renderer.render(result)
        assert single_citation.formatted_text in output

    def test_single_citation_url_appears_in_output(
        self,
        renderer: MarkdownRendererAdapter,
        single_citation: Citation,
    ) -> None:
        """A single citation's URL must appear in the output."""
        result = _make_result(citations=(single_citation,))
        output = renderer.render(result)
        assert single_citation.url in output

    def test_citation_line_format_includes_em_dash_separator(
        self,
        renderer: MarkdownRendererAdapter,
        single_citation: Citation,
    ) -> None:
        """Citation lines must use ' — ' to separate formatted_text from url."""
        result = _make_result(citations=(single_citation,))
        output = renderer.render(result)
        expected_line = f"{single_citation.formatted_text} \u2014 {single_citation.url}"
        assert expected_line in output

    def test_multiple_citations_all_present(
        self,
        renderer: MarkdownRendererAdapter,
        two_citations: tuple[Citation, ...],
    ) -> None:
        """All citations in a multi-citation result must appear in the output."""
        result = _make_result(citations=two_citations)
        output = renderer.render(result)
        for citation in two_citations:
            assert citation.url in output

    def test_citation_index_present_for_each_citation(
        self,
        renderer: MarkdownRendererAdapter,
        two_citations: tuple[Citation, ...],
    ) -> None:
        """Each citation's 1-based index must appear before its text."""
        result = _make_result(citations=two_citations)
        output = renderer.render(result)
        for citation in two_citations:
            assert f"{citation.index}." in output

    def test_no_citations_produces_fallback_message(
        self,
        renderer: MarkdownRendererAdapter,
    ) -> None:
        """An empty citations tuple must produce the 'No sources were cited.' note."""
        result = _make_result(citations=())
        output = renderer.render(result)
        assert "No sources were cited." in output


# ---------------------------------------------------------------------------
# Footer statistics tests
# ---------------------------------------------------------------------------


class TestRenderFooter:
    """Tests for the statistics footer line."""

    def test_footer_contains_sources_found(
        self, renderer: MarkdownRendererAdapter
    ) -> None:
        """Footer must report the total_sources_found count."""
        result = _make_result(total_sources_found=7)
        output = renderer.render(result)
        assert "7" in output

    def test_footer_contains_iterations_performed(
        self, renderer: MarkdownRendererAdapter
    ) -> None:
        """Footer must report the iterations_performed count."""
        result = _make_result(iterations_performed=4)
        output = renderer.render(result)
        assert "4" in output

    def test_footer_duration_formatted_to_two_decimal_places(
        self, renderer: MarkdownRendererAdapter
    ) -> None:
        """Duration must appear as 'X.XXs' (two decimal places)."""
        result = _make_result(duration_seconds=3.14159)
        output = renderer.render(result)
        assert "3.14s" in output

    def test_footer_duration_zero_formatted_correctly(
        self, renderer: MarkdownRendererAdapter
    ) -> None:
        """A zero duration must render as '0.00s'."""
        result = _make_result(duration_seconds=0.0)
        output = renderer.render(result)
        assert "0.00s" in output

    def test_footer_contains_sources_label(
        self, renderer: MarkdownRendererAdapter
    ) -> None:
        """Footer must contain the 'Sources found:' label text."""
        result = _make_result()
        output = renderer.render(result)
        assert "Sources found:" in output

    def test_footer_contains_iterations_label(
        self, renderer: MarkdownRendererAdapter
    ) -> None:
        """Footer must contain the 'Iterations:' label text."""
        result = _make_result()
        output = renderer.render(result)
        assert "Iterations:" in output

    def test_footer_contains_duration_label(
        self, renderer: MarkdownRendererAdapter
    ) -> None:
        """Footer must contain the 'Duration:' label text."""
        result = _make_result()
        output = renderer.render(result)
        assert "Duration:" in output

    def test_footer_is_rendered_as_italic_markdown(
        self, renderer: MarkdownRendererAdapter
    ) -> None:
        """Footer line must be wrapped in Markdown italic asterisks."""
        result = _make_result()
        output = renderer.render(result)
        # The footer line begins and ends with '*'
        footer_line = [line for line in output.splitlines() if "Sources found:" in line]
        assert footer_line, "Footer line not found in output"
        assert footer_line[0].startswith("*")
        assert footer_line[0].endswith("*")
