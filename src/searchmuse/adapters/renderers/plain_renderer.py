"""Plain text renderer adapter implementing ResultRendererPort.

Produces a simple unformatted text representation of a SearchResult,
suitable for plain terminal output or text file export.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from searchmuse.domain.models import SearchResult


class PlainRendererAdapter:
    """Renders a SearchResult as unformatted plain text.

    Implements the ``ResultRendererPort`` protocol.
    """

    @property
    def format_name(self) -> str:
        return "plain"

    def render(self, result: SearchResult) -> str:
        """Render a completed search result to plain text.

        Args:
            result: The frozen SearchResult to render.

        Returns:
            A plain text string with answer, sources, and footer.
        """
        lines: list[str] = [
            "ANSWER",
            "=" * 60,
            result.synthesis,
            "",
            "SOURCES",
            "=" * 60,
        ]

        if result.citations:
            for citation in result.citations:
                lines.append(f"  {citation.index}. {citation.formatted_text}")
                lines.append(f"     {citation.url}")
        else:
            lines.append("  No sources were cited.")

        lines.append("")
        lines.append("-" * 60)
        duration = f"{result.duration_seconds:.2f}s"
        lines.append(
            f"Sources found: {result.total_sources_found} | "
            f"Iterations: {result.iterations_performed} | "
            f"Duration: {duration}"
        )

        return "\n".join(lines)
