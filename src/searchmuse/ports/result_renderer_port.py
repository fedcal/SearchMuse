"""Protocol definition for result renderer adapter port."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from searchmuse.domain.models import SearchResult


@runtime_checkable
class ResultRendererPort(Protocol):
    """Abstract port for rendering a SearchResult to a string representation.

    Implementations cover output formats such as Markdown, JSON, and plain text.
    """

    def render(self, result: SearchResult) -> str:
        """Render a completed search result to a string.

        Args:
            result: The frozen SearchResult to render.

        Returns:
            A formatted string representation of the result.
        """
        ...

    @property
    def format_name(self) -> str:
        """Human-readable name of the output format.

        Returns:
            A short format identifier, e.g. "markdown", "json", "plain".
        """
        ...
