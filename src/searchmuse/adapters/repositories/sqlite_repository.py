"""SQLite-backed source repository adapter implementing SourceRepositoryPort.

Uses ``aiosqlite`` for non-blocking database access within the asyncio event
loop.  The connection and table are created lazily on the first operation via
``_ensure_db()``, so construction is always synchronous and lightweight.

All ``aiosqlite`` exceptions are caught and re-raised as ``StorageError`` to
keep the domain layer insulated from the persistence library.
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

import aiosqlite

from searchmuse.domain.enums import RelevanceScore
from searchmuse.domain.errors import StorageError
from searchmuse.domain.models import Source

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Internal constants
# ---------------------------------------------------------------------------

_CREATE_TABLE_SQL: str = """
CREATE TABLE IF NOT EXISTS sources (
    source_id        TEXT PRIMARY KEY,
    session_id       TEXT NOT NULL,
    content_id       TEXT NOT NULL,
    url              TEXT NOT NULL,
    title            TEXT NOT NULL,
    snippet          TEXT NOT NULL,
    relevance_score  TEXT NOT NULL,
    credibility_notes TEXT NOT NULL,
    author           TEXT,
    accessed_at      TEXT NOT NULL
)
"""

_CREATE_SCRAPED_PAGES_SQL: str = """
CREATE TABLE IF NOT EXISTS scraped_pages (
    page_id          TEXT PRIMARY KEY,
    session_id       TEXT NOT NULL,
    url              TEXT NOT NULL,
    raw_html         TEXT NOT NULL,
    http_status      INTEGER NOT NULL,
    content_type     TEXT NOT NULL,
    scraped_at       TEXT NOT NULL
)
"""

_INSERT_SCRAPED_PAGE_SQL: str = """
INSERT OR REPLACE INTO scraped_pages (
    page_id, session_id, url, raw_html, http_status, content_type, scraped_at
) VALUES (?, ?, ?, ?, ?, ?, ?)
"""

_UPSERT_SQL: str = """
INSERT OR REPLACE INTO sources (
    source_id, session_id, content_id, url, title, snippet,
    relevance_score, credibility_notes, author, accessed_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

_SELECT_BY_ID_SQL: str = """
SELECT source_id, session_id, content_id, url, title, snippet,
       relevance_score, credibility_notes, author, accessed_at
FROM sources
WHERE source_id = ?
"""

_SELECT_BY_SESSION_SQL: str = """
SELECT source_id, session_id, content_id, url, title, snippet,
       relevance_score, credibility_notes, author, accessed_at
FROM sources
WHERE session_id = ?
"""

_SELECT_BY_URL_SQL: str = """
SELECT source_id, session_id, content_id, url, title, snippet,
       relevance_score, credibility_notes, author, accessed_at
FROM sources
WHERE url = ?
ORDER BY accessed_at DESC
LIMIT 1
"""


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _row_to_source(row: aiosqlite.Row) -> Source:
    """Reconstruct an immutable :class:`Source` from a database row.

    Args:
        row: A row returned by an ``aiosqlite`` cursor, addressable by index.

    Returns:
        A new, frozen :class:`Source` instance with all fields populated.
    """
    return Source(
        source_id=row[0],
        # row[1] is session_id — not part of the Source dataclass, skipped.
        content_id=row[2],
        url=row[3],
        title=row[4],
        snippet=row[5],
        relevance_score=RelevanceScore(row[6]),
        credibility_notes=row[7],
        author=row[8] if row[8] is not None else None,
        accessed_at=datetime.fromisoformat(row[9]),
    )


# ---------------------------------------------------------------------------
# Adapter
# ---------------------------------------------------------------------------


class SqliteRepositoryAdapter:
    """SQLite-backed implementation of ``SourceRepositoryPort``.

    The database file and ``sources`` table are created automatically on first
    use.  Parent directories are created if they do not already exist.

    Args:
        db_path: Absolute path to the SQLite file, after expanding ``~``.
            Construct instances via :meth:`from_config` when working with a
            :class:`StorageConfig` object, or pass the expanded path directly.

    Example::

        adapter = SqliteRepositoryAdapter(db_path="/home/user/.searchmuse/searchmuse.db")
        await adapter.save(source, session_id="abc123")
        sources = await adapter.find_by_session("abc123")
        await adapter.close()
    """

    def __init__(self, db_path: str, *, store_raw_html: bool = False) -> None:
        """Initialise the adapter with the resolved database path.

        Args:
            db_path: Filesystem path to the SQLite database file.
                Use :func:`os.path.expanduser` or :class:`pathlib.Path`
                expansion before passing the value here.
            store_raw_html: When True, enables the ``save_raw_html`` method
                and creates the ``scraped_pages`` table.
        """
        self._db_path: Path = Path(db_path).expanduser().resolve()
        self._connection: aiosqlite.Connection | None = None
        self._store_raw_html: bool = store_raw_html

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @classmethod
    def from_config(cls, config: object) -> SqliteRepositoryAdapter:
        """Construct an adapter from a ``StorageConfig``-like object.

        Args:
            config: Any object exposing a ``db_path`` attribute (str).

        Returns:
            A new :class:`SqliteRepositoryAdapter` with the expanded path.
        """
        raw_path: str = str(getattr(config, "db_path", ""))
        expanded: str = str(Path(raw_path).expanduser())
        return cls(db_path=expanded)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def _ensure_db(self) -> aiosqlite.Connection:
        """Return the open connection, creating it and the schema if needed.

        Creates all parent directories for the database file before opening
        so that first-run setups work without manual directory creation.

        Returns:
            An open :class:`aiosqlite.Connection` ready for queries.

        Raises:
            StorageError: When the database cannot be opened or the table
                cannot be created.
        """
        if self._connection is not None:
            return self._connection

        try:
            self._db_path.parent.mkdir(parents=True, exist_ok=True)
            connection: aiosqlite.Connection = await aiosqlite.connect(str(self._db_path))
            connection.row_factory = aiosqlite.Row
            await connection.execute(_CREATE_TABLE_SQL)
            if self._store_raw_html:
                await connection.execute(_CREATE_SCRAPED_PAGES_SQL)
            await connection.commit()
            self._connection = connection
            logger.debug("SQLite database opened at %s", self._db_path)
        except aiosqlite.Error as exc:
            raise StorageError(
                f"Failed to initialise SQLite database at {self._db_path}: {exc}"
            ) from exc

        return self._connection

    async def close(self) -> None:
        """Close the underlying SQLite connection if it is open.

        Safe to call multiple times; subsequent calls are no-ops.
        """
        if self._connection is not None:
            try:
                await self._connection.close()
            except aiosqlite.Error as exc:
                logger.warning("Error while closing SQLite connection: %s", exc)
            finally:
                self._connection = None
                logger.debug("SQLite connection closed")

    # ------------------------------------------------------------------
    # Raw HTML storage
    # ------------------------------------------------------------------

    async def save_raw_html(
        self,
        page_id: str,
        session_id: str,
        url: str,
        raw_html: str,
        http_status: int,
        content_type: str,
        scraped_at: datetime,
    ) -> None:
        """Persist scraped raw HTML when ``store_raw_html`` is enabled.

        Args:
            page_id: Unique page identifier.
            session_id: Search session identifier.
            url: The fetched URL.
            raw_html: Full raw HTML body.
            http_status: HTTP response status code.
            content_type: MIME content type string.
            scraped_at: UTC timestamp of the scrape.

        Raises:
            StorageError: When the insert fails.
        """
        if not self._store_raw_html:
            return

        conn = await self._ensure_db()
        params = (
            page_id,
            session_id,
            url,
            raw_html,
            http_status,
            content_type,
            scraped_at.isoformat(),
        )
        try:
            await conn.execute(_INSERT_SCRAPED_PAGE_SQL, params)
            await conn.commit()
            logger.debug("Saved raw HTML for page %s", page_id)
        except aiosqlite.Error as exc:
            raise StorageError(
                f"Failed to save raw HTML for page {page_id!r}: {exc}"
            ) from exc

    # ------------------------------------------------------------------
    # SourceRepositoryPort implementation
    # ------------------------------------------------------------------

    async def save(self, source: Source, session_id: str = "") -> None:
        """Persist a source record, replacing any existing row with the same ID.

        The ``session_id`` is stored alongside the source fields to support
        efficient session-scoped queries via :meth:`find_by_session`.

        Args:
            source: The frozen :class:`Source` to persist.
            session_id: Identifier of the search session that produced this
                source.  Defaults to ``""`` for backwards compatibility.

        Raises:
            StorageError: When the upsert operation fails.
        """
        conn = await self._ensure_db()
        params = (
            source.source_id,
            session_id,
            source.content_id,
            source.url,
            source.title,
            source.snippet,
            str(source.relevance_score),
            source.credibility_notes,
            source.author,
            source.accessed_at.isoformat(),
        )
        try:
            await conn.execute(_UPSERT_SQL, params)
            await conn.commit()
            logger.debug("Saved source %s to session %r", source.source_id, session_id)
        except aiosqlite.Error as exc:
            raise StorageError(
                f"Failed to save source {source.source_id!r}: {exc}"
            ) from exc

    async def find_by_id(self, source_id: str) -> Source | None:
        """Retrieve a source by its unique identifier.

        Args:
            source_id: The primary key to look up.

        Returns:
            The matching :class:`Source`, or ``None`` when not found.

        Raises:
            StorageError: When the query fails due to a database error.
        """
        conn = await self._ensure_db()
        try:
            async with conn.execute(_SELECT_BY_ID_SQL, (source_id,)) as cursor:
                row = await cursor.fetchone()
        except aiosqlite.Error as exc:
            raise StorageError(
                f"Failed to query source by id {source_id!r}: {exc}"
            ) from exc

        if row is None:
            return None
        return _row_to_source(row)

    async def find_by_session(self, session_id: str) -> tuple[Source, ...]:
        """Retrieve all sources associated with a search session.

        Args:
            session_id: The session identifier to filter by.

        Returns:
            An immutable tuple of matching :class:`Source` objects, possibly
            empty when no sources have been saved under the given session.

        Raises:
            StorageError: When the query fails due to a database error.
        """
        conn = await self._ensure_db()
        try:
            async with conn.execute(_SELECT_BY_SESSION_SQL, (session_id,)) as cursor:
                rows = await cursor.fetchall()
        except aiosqlite.Error as exc:
            raise StorageError(
                f"Failed to query sources for session {session_id!r}: {exc}"
            ) from exc

        return tuple(_row_to_source(row) for row in rows)

    async def find_by_url(self, url: str) -> Source | None:
        """Retrieve the most recently saved source for a given URL.

        Useful for deduplication: callers can check whether a URL has already
        been processed before issuing a new scrape request.

        Args:
            url: The exact URL to look up.

        Returns:
            The most recent :class:`Source` for that URL, or ``None``.

        Raises:
            StorageError: When the query fails due to a database error.
        """
        conn = await self._ensure_db()
        try:
            async with conn.execute(_SELECT_BY_URL_SQL, (url,)) as cursor:
                row = await cursor.fetchone()
        except aiosqlite.Error as exc:
            raise StorageError(
                f"Failed to query source by url {url!r}: {exc}"
            ) from exc

        if row is None:
            return None
        return _row_to_source(row)
