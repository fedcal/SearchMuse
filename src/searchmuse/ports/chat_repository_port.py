"""Protocol definition for chat repository adapter port."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from searchmuse.domain.models import ChatMessage, ChatSession


@runtime_checkable
class ChatRepositoryPort(Protocol):
    """Abstract port for persisting and querying chat sessions and messages.

    Implementations may use SQLite, an in-memory store, or any other
    backend. All methods raise StorageError on failure.
    """

    async def create_session(self, session: ChatSession) -> None:
        """Persist a new chat session record.

        Args:
            session: The frozen ChatSession to persist.
        """
        ...

    async def save_message(self, session_id: str, message: ChatMessage) -> None:
        """Persist a chat message within a session.

        Args:
            session_id: The parent session identifier.
            message: The frozen ChatMessage to persist.
        """
        ...

    async def update_session_name(self, session_id: str, name: str) -> None:
        """Update the display name of an existing session.

        Args:
            session_id: The session to rename.
            name: The new session name.
        """
        ...

    async def update_session_timestamp(self, session_id: str) -> None:
        """Update the updated_at timestamp of a session to now.

        Args:
            session_id: The session to touch.
        """
        ...

    async def load_session(self, session_id: str) -> ChatSession | None:
        """Load a full chat session with all its messages.

        Args:
            session_id: The session identifier to load.

        Returns:
            The ChatSession with messages, or None if not found.
        """
        ...

    async def list_sessions(self) -> tuple[ChatSession, ...]:
        """List all chat sessions ordered by updated_at descending.

        Returns:
            A tuple of ChatSession objects (messages may be empty tuples
            for listing purposes).
        """
        ...

    async def delete_session(self, session_id: str) -> None:
        """Delete a chat session and all its messages.

        Args:
            session_id: The session to delete.
        """
        ...

    async def find_session_by_name(self, name: str) -> ChatSession | None:
        """Find a session by partial name match (case-insensitive).

        Args:
            name: The name fragment to search for.

        Returns:
            The first matching ChatSession, or None.
        """
        ...

    async def close(self) -> None:
        """Release any held resources."""
        ...
