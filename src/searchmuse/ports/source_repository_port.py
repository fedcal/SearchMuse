"""Protocol definition for source repository adapter port."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from searchmuse.domain.models import Source


@runtime_checkable
class SourceRepositoryPort(Protocol):
    """Abstract port for persisting and querying Source records.

    Implementations may use SQLite (via aiosqlite), an in-memory store,
    or any other backend. All methods raise StorageError on failure.
    """

    async def save(self, source: Source) -> None:
        """Persist a source record.

        Performs an upsert: if a source with the same source_id already
        exists, it is replaced; otherwise a new record is created.

        Args:
            source: The frozen Source to persist.
        """
        ...

    async def find_by_id(self, source_id: str) -> Source | None:
        """Retrieve a source by its unique identifier.

        Args:
            source_id: The source_id to look up.

        Returns:
            The matching Source, or None if not found.
        """
        ...

    async def find_by_session(self, session_id: str) -> tuple[Source, ...]:
        """Retrieve all sources associated with a search session.

        Args:
            session_id: The session identifier to filter by.

        Returns:
            A tuple of matching Source objects, possibly empty.
        """
        ...

    async def find_by_url(self, url: str) -> Source | None:
        """Retrieve a source by its URL.

        Useful for deduplication before scraping the same URL twice.

        Args:
            url: The exact URL to look up.

        Returns:
            The most recently saved Source for that URL, or None.
        """
        ...
