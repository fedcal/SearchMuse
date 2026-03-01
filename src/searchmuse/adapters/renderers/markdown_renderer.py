"""Markdown renderer adapter implementing ResultRendererPort.

Converts a completed :class:`SearchResult` into a structured Markdown document
suitable for terminal display, file export, or downstream Markdown processors.

Document layout::

    ## Answer
    <synthesis narrative>

    ## Sources
    1. <formatted_text> — <url>
    2. …

    ---
    *Sources found: N · Iterations: N · Duration: N.NNs*
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from searchmuse.domain.models import SearchResult

# ---------------------------------------------------------------------------
# Internal constants
# ---------------------------------------------------------------------------

_SECTION_ANSWER: str = "## Answer"
_SECTION_SOURCES: str = "## Sources"
_SEPARATOR: str = "---"
_SECTION_SEPARATOR: str = _SEPARATOR


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _render_citations(result: SearchResult) -> str:
    """Render the numbered citations block.

    Args:
        result: The completed search result containing citations.

    Returns:
        A Markdown-formatted string with one citation per line, or a
        fallback message when no citations are available.
    """
    if not result.citations:
        return "*No sources were cited.*"

    lines: list[str] = []
    for citation in result.citations:
        lines.append(f"{citation.index}. {citation.formatted_text} — {citation.url}")
        if citation.snippet:
            lines.append(f"   > {citation.snippet}")
    return "\n".join(lines)


def _render_footer(result: SearchResult) -> str:
    """Render the statistics footer line.

    Args:
        result: The completed search result containing run statistics.

    Returns:
        A Markdown italic line summarising sources, iterations, and duration.
    """
    duration_formatted = f"{result.duration_seconds:.2f}s"
    return (
        f"*Sources found: {result.total_sources_found}"
        f" \u00b7 Iterations: {result.iterations_performed}"
        f" \u00b7 Duration: {duration_formatted}*"
    )


# ---------------------------------------------------------------------------
# Adapter
# ---------------------------------------------------------------------------


class MarkdownRendererAdapter:
    """Renders a :class:`SearchResult` as a structured Markdown document.

    Implements the ``ResultRendererPort`` protocol.  No configuration is
    required; instantiate directly and call :meth:`render`.

    Example::

        renderer = MarkdownRendererAdapter()
        markdown_text = renderer.render(result)
        print(markdown_text)
    """

    @property
    def format_name(self) -> str:
        """Human-readable format identifier for this renderer.

        Returns:
            The string ``"markdown"``.
        """
        return "markdown"

    def render(self, result: SearchResult) -> str:
        """Render a completed search result to a Markdown string.

        Produces a document with an **Answer** section containing the
        LLM synthesis, a **Sources** section with numbered citations, a
        horizontal rule separator, and a footer summarising run statistics.

        Args:
            result: The frozen :class:`SearchResult` to render.

        Returns:
            A complete Markdown string ready for display or file export.
        """
        sections: list[str] = [
            _SECTION_ANSWER,
            result.synthesis,
            "",
            _SECTION_SOURCES,
            _render_citations(result),
            "",
            _SECTION_SEPARATOR,
            _render_footer(result),
        ]
        return "\n".join(sections)

