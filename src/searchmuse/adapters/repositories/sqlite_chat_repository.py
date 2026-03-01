"""SQLite-backed chat repository adapter implementing ChatRepositoryPort.

Uses ``aiosqlite`` for non-blocking database access.  The connection and
tables are created lazily on the first operation via ``_ensure_db()``.

All ``aiosqlite`` exceptions are caught and re-raised as ``StorageError``.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path

import aiosqlite

from searchmuse.domain.errors import StorageError
from searchmuse.domain.models import ChatMessage, ChatSession

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# SQL constants
# ---------------------------------------------------------------------------

_CREATE_SESSIONS_SQL: str = """
CREATE TABLE IF NOT EXISTS chat_sessions (
    session_id TEXT PRIMARY KEY,
    name       TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
"""

_CREATE_MESSAGES_SQL: str = """
CREATE TABLE IF NOT EXISTS chat_messages (
    message_id  TEXT PRIMARY KEY,
    session_id  TEXT NOT NULL REFERENCES chat_sessions(session_id),
    role        TEXT NOT NULL,
    content     TEXT NOT NULL,
    result_json TEXT NOT NULL DEFAULT '',
    created_at  TEXT NOT NULL
)
"""

_INSERT_SESSION_SQL: str = """
INSERT OR REPLACE INTO chat_sessions (session_id, name, created_at, updated_at)
VALUES (?, ?, ?, ?)
"""

_INSERT_MESSAGE_SQL: str = """
INSERT OR REPLACE INTO chat_messages
    (message_id, session_id, role, content, result_json, created_at)
VALUES (?, ?, ?, ?, ?, ?)
"""

_UPDATE_SESSION_NAME_SQL: str = """
UPDATE chat_sessions SET name = ?, updated_at = ? WHERE session_id = ?
"""

_UPDATE_SESSION_TIMESTAMP_SQL: str = """
UPDATE chat_sessions SET updated_at = ? WHERE session_id = ?
"""

_SELECT_SESSION_SQL: str = """
SELECT session_id, name, created_at, updated_at
FROM chat_sessions WHERE session_id = ?
"""

_SELECT_MESSAGES_SQL: str = """
SELECT message_id, session_id, role, content, result_json, created_at
FROM chat_messages WHERE session_id = ? ORDER BY created_at ASC
"""

_LIST_SESSIONS_SQL: str = """
SELECT session_id, name, created_at, updated_at
FROM chat_sessions ORDER BY updated_at DESC
"""

_COUNT_MESSAGES_SQL: str = """
SELECT COUNT(*) FROM chat_messages WHERE session_id = ?
"""

_DELETE_MESSAGES_SQL: str = """
DELETE FROM chat_messages WHERE session_id = ?
"""

_DELETE_SESSION_SQL: str = """
DELETE FROM chat_sessions WHERE session_id = ?
"""

_FIND_BY_NAME_SQL: str = """
SELECT session_id, name, created_at, updated_at
FROM chat_sessions WHERE LOWER(name) LIKE ? ORDER BY updated_at DESC LIMIT 1
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _row_to_message(row: aiosqlite.Row) -> ChatMessage:
    """Reconstruct a ChatMessage from a database row."""
    return ChatMessage(
        message_id=row[0],
        role=row[2],
        content=row[3],
        created_at=datetime.fromisoformat(row[5]),
        result_json=row[4],
    )


def _row_to_session(row: aiosqlite.Row, messages: tuple[ChatMessage, ...] = ()) -> ChatSession:
    """Reconstruct a ChatSession from a database row."""
    return ChatSession(
        session_id=row[0],
        name=row[1],
        messages=messages,
        created_at=datetime.fromisoformat(row[2]),
        updated_at=datetime.fromisoformat(row[3]),
    )


def _now_iso() -> str:
    """Return current UTC datetime as ISO string."""
    return datetime.now(UTC).isoformat()


# ---------------------------------------------------------------------------
# Adapter
# ---------------------------------------------------------------------------


class SqliteChatRepositoryAdapter:
    """SQLite-backed implementation of ``ChatRepositoryPort``.

    Manages ``chat_sessions`` and ``chat_messages`` tables in the same
    database file used for source storage.
    """

    def __init__(self, db_path: str) -> None:
        self._db_path: Path = Path(db_path).expanduser().resolve()
        self._connection: aiosqlite.Connection | None = None

    @classmethod
    def from_config(cls, config: object) -> SqliteChatRepositoryAdapter:
        """Construct from a config object with a ``db_path`` attribute."""
        raw_path: str = str(getattr(config, "db_path", ""))
        expanded: str = str(Path(raw_path).expanduser())
        return cls(db_path=expanded)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def _ensure_db(self) -> aiosqlite.Connection:
        """Return the open connection, creating schema if needed."""
        if self._connection is not None:
            return self._connection

        try:
            self._db_path.parent.mkdir(parents=True, exist_ok=True)
            connection = await aiosqlite.connect(str(self._db_path))
            connection.row_factory = aiosqlite.Row
            await connection.execute(_CREATE_SESSIONS_SQL)
            await connection.execute(_CREATE_MESSAGES_SQL)
            await connection.commit()
            self._connection = connection
            logger.debug("Chat SQLite database opened at %s", self._db_path)
        except aiosqlite.Error as exc:
            raise StorageError(
                f"Failed to initialise chat SQLite database at {self._db_path}: {exc}"
            ) from exc

        return self._connection

    async def close(self) -> None:
        """Close the underlying SQLite connection if open."""
        if self._connection is not None:
            try:
                await self._connection.close()
            except aiosqlite.Error as exc:
                logger.warning("Error closing chat SQLite connection: %s", exc)
            finally:
                self._connection = None

    # ------------------------------------------------------------------
    # ChatRepositoryPort implementation
    # ------------------------------------------------------------------

    async def create_session(self, session: ChatSession) -> None:
        """Persist a new chat session."""
        conn = await self._ensure_db()
        params = (
            session.session_id,
            session.name,
            session.created_at.isoformat(),
            session.updated_at.isoformat(),
        )
        try:
            await conn.execute(_INSERT_SESSION_SQL, params)
            await conn.commit()
        except aiosqlite.Error as exc:
            raise StorageError(
                f"Failed to create chat session {session.session_id!r}: {exc}"
            ) from exc

    async def save_message(self, session_id: str, message: ChatMessage) -> None:
        """Persist a chat message within a session."""
        conn = await self._ensure_db()
        params = (
            message.message_id,
            session_id,
            message.role,
            message.content,
            message.result_json,
            message.created_at.isoformat(),
        )
        try:
            await conn.execute(_INSERT_MESSAGE_SQL, params)
            await conn.commit()
        except aiosqlite.Error as exc:
            raise StorageError(
                f"Failed to save chat message {message.message_id!r}: {exc}"
            ) from exc

    async def update_session_name(self, session_id: str, name: str) -> None:
        """Update the display name of an existing session."""
        conn = await self._ensure_db()
        try:
            await conn.execute(_UPDATE_SESSION_NAME_SQL, (name, _now_iso(), session_id))
            await conn.commit()
        except aiosqlite.Error as exc:
            raise StorageError(
                f"Failed to rename chat session {session_id!r}: {exc}"
            ) from exc

    async def update_session_timestamp(self, session_id: str) -> None:
        """Touch the updated_at timestamp of a session."""
        conn = await self._ensure_db()
        try:
            await conn.execute(_UPDATE_SESSION_TIMESTAMP_SQL, (_now_iso(), session_id))
            await conn.commit()
        except aiosqlite.Error as exc:
            raise StorageError(
                f"Failed to update timestamp for session {session_id!r}: {exc}"
            ) from exc

    async def load_session(self, session_id: str) -> ChatSession | None:
        """Load a full chat session with all its messages."""
        conn = await self._ensure_db()
        try:
            async with conn.execute(_SELECT_SESSION_SQL, (session_id,)) as cursor:
                session_row = await cursor.fetchone()

            if session_row is None:
                return None

            async with conn.execute(_SELECT_MESSAGES_SQL, (session_id,)) as cursor:
                message_rows = await cursor.fetchall()

            messages = tuple(_row_to_message(row) for row in message_rows)
            return _row_to_session(session_row, messages)

        except aiosqlite.Error as exc:
            raise StorageError(
                f"Failed to load chat session {session_id!r}: {exc}"
            ) from exc

    async def list_sessions(self) -> tuple[ChatSession, ...]:
        """List all chat sessions ordered by updated_at descending."""
        conn = await self._ensure_db()
        try:
            async with conn.execute(_LIST_SESSIONS_SQL) as cursor:
                session_rows = await cursor.fetchall()

            sessions: list[ChatSession] = []
            for row in session_rows:
                sid = row[0]
                async with conn.execute(_COUNT_MESSAGES_SQL, (sid,)) as cursor:
                    count_row = await cursor.fetchone()
                msg_count = count_row[0] if count_row else 0

                # Build a placeholder tuple with the right length for display
                placeholder_messages: tuple[ChatMessage, ...] = tuple(
                    ChatMessage(
                        message_id="",
                        role="user",
                        content="",
                        created_at=datetime.fromisoformat(row[2]),
                    )
                    for _ in range(msg_count)
                )
                sessions.append(_row_to_session(row, placeholder_messages))

            return tuple(sessions)

        except aiosqlite.Error as exc:
            raise StorageError(f"Failed to list chat sessions: {exc}") from exc

    async def delete_session(self, session_id: str) -> None:
        """Delete a chat session and all its messages."""
        conn = await self._ensure_db()
        try:
            await conn.execute(_DELETE_MESSAGES_SQL, (session_id,))
            await conn.execute(_DELETE_SESSION_SQL, (session_id,))
            await conn.commit()
        except aiosqlite.Error as exc:
            raise StorageError(
                f"Failed to delete chat session {session_id!r}: {exc}"
            ) from exc

    async def find_session_by_name(self, name: str) -> ChatSession | None:
        """Find a session by partial name match (case-insensitive)."""
        conn = await self._ensure_db()
        try:
            pattern = f"%{name.lower()}%"
            async with conn.execute(_FIND_BY_NAME_SQL, (pattern,)) as cursor:
                session_row = await cursor.fetchone()

            if session_row is None:
                return None

            sid = session_row[0]
            async with conn.execute(_SELECT_MESSAGES_SQL, (sid,)) as cursor:
                message_rows = await cursor.fetchall()

            messages = tuple(_row_to_message(row) for row in message_rows)
            return _row_to_session(session_row, messages)

        except aiosqlite.Error as exc:
            raise StorageError(
                f"Failed to find chat session by name {name!r}: {exc}"
            ) from exc
