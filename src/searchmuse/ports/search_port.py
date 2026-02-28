"""Protocol definition for web search engine adapter port."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from searchmuse.domain.models import SearchHit


@runtime_checkable
class SearchPort(Protocol):
    """Abstract port for querying a web search engine.

    Implementations wrap search backends such as DuckDuckGo, Google, etc.
    All async methods raise ScrapingError subclasses on failure.
    """

    async def search(
        self,
        query: str,
        *,
        max_results: int = 10,
    ) -> tuple[SearchHit, ...]:
        """Execute a search query and return raw hits.

        Args:
            query: The search terms to look up.
            max_results: Maximum number of results to return.

        Returns:
            A tuple of SearchHit instances with URLs, titles, and snippets.
        """
        ...

    async def close(self) -> None:
        """Release any held resources.

        Must be idempotent; calling close() on an already-closed
        adapter must not raise.
        """
        ...
