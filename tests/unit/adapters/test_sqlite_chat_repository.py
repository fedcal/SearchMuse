"""Unit tests for SqliteChatRepositoryAdapter.

Uses a temporary on-disk SQLite database (via tmp_path) so each test gets a
clean slate. All async tests run via asyncio_mode = "auto" (pytest-asyncio).
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path  # noqa: TC003 - used at runtime by pytest tmp_path fixtures

import pytest

from searchmuse.adapters.repositories.sqlite_chat_repository import (
    SqliteChatRepositoryAdapter,
)
from searchmuse.domain.models import ChatMessage, ChatSession

_NOW = datetime(2024, 6, 1, 12, 0, 0, tzinfo=UTC)
_LATER = datetime(2024, 6, 2, 8, 0, 0, tzinfo=UTC)


def _make_session(
    *,
    session_id: str = "sess-001",
    name: str = "test-chat",
    created_at: datetime = _NOW,
    updated_at: datetime = _NOW,
) -> ChatSession:
    return ChatSession(
        session_id=session_id,
        name=name,
        messages=(),
        created_at=created_at,
        updated_at=updated_at,
    )


def _make_message(
    *,
    message_id: str = "msg-001",
    role: str = "user",
    content: str = "What is quantum computing?",
    created_at: datetime = _NOW,
    result_json: str = "",
) -> ChatMessage:
    return ChatMessage(
        message_id=message_id,
        role=role,
        content=content,
        created_at=created_at,
        result_json=result_json,
    )


@pytest.fixture()
async def repo(tmp_path: Path) -> SqliteChatRepositoryAdapter:
    db_file = tmp_path / "test_chat.db"
    adapter = SqliteChatRepositoryAdapter(db_path=str(db_file))
    yield adapter  # type: ignore[misc]
    await adapter.close()


class TestCreateAndLoadSession:
    """create_session + load_session round-trip."""

    async def test_round_trip_returns_session(
        self, repo: SqliteChatRepositoryAdapter
    ) -> None:
        session = _make_session()
        await repo.create_session(session)
        result = await repo.load_session(session.session_id)
        assert result is not None
        assert result.session_id == session.session_id

    async def test_round_trip_name_matches(
        self, repo: SqliteChatRepositoryAdapter
    ) -> None:
        session = _make_session(name="my-research")
        await repo.create_session(session)
        result = await repo.load_session(session.session_id)
        assert result is not None
        assert result.name == "my-research"

    async def test_round_trip_empty_messages(
        self, repo: SqliteChatRepositoryAdapter
    ) -> None:
        session = _make_session()
        await repo.create_session(session)
        result = await repo.load_session(session.session_id)
        assert result is not None
        assert result.messages == ()

    async def test_load_returns_none_for_unknown(
        self, repo: SqliteChatRepositoryAdapter
    ) -> None:
        result = await repo.load_session("nonexistent")
        assert result is None


class TestSaveAndLoadMessages:
    """save_message + load_session must return messages in order."""

    async def test_messages_returned_in_order(
        self, repo: SqliteChatRepositoryAdapter
    ) -> None:
        session = _make_session()
        await repo.create_session(session)

        msg_user = _make_message(message_id="m1", role="user", content="query")
        msg_assistant = _make_message(
            message_id="m2",
            role="assistant",
            content="answer",
            created_at=_LATER,
        )

        await repo.save_message(session.session_id, msg_user)
        await repo.save_message(session.session_id, msg_assistant)

        result = await repo.load_session(session.session_id)
        assert result is not None
        assert len(result.messages) == 2
        assert result.messages[0].role == "user"
        assert result.messages[1].role == "assistant"

    async def test_message_content_preserved(
        self, repo: SqliteChatRepositoryAdapter
    ) -> None:
        session = _make_session()
        await repo.create_session(session)

        msg = _make_message(content="specific content text")
        await repo.save_message(session.session_id, msg)

        result = await repo.load_session(session.session_id)
        assert result is not None
        assert result.messages[0].content == "specific content text"

    async def test_result_json_preserved(
        self, repo: SqliteChatRepositoryAdapter
    ) -> None:
        session = _make_session()
        await repo.create_session(session)

        msg = _make_message(
            role="assistant",
            result_json='{"synthesis": "answer text"}',
        )
        await repo.save_message(session.session_id, msg)

        result = await repo.load_session(session.session_id)
        assert result is not None
        assert result.messages[0].result_json == '{"synthesis": "answer text"}'


class TestUpdateSessionName:
    """update_session_name must change the display name."""

    async def test_name_is_updated(
        self, repo: SqliteChatRepositoryAdapter
    ) -> None:
        session = _make_session(name="old-name")
        await repo.create_session(session)

        await repo.update_session_name(session.session_id, "new-name")

        result = await repo.load_session(session.session_id)
        assert result is not None
        assert result.name == "new-name"


class TestListSessions:
    """list_sessions must return all sessions ordered by updated_at."""

    async def test_returns_all_sessions(
        self, repo: SqliteChatRepositoryAdapter
    ) -> None:
        s1 = _make_session(session_id="s1", name="first")
        s2 = _make_session(session_id="s2", name="second", updated_at=_LATER)
        await repo.create_session(s1)
        await repo.create_session(s2)

        sessions = await repo.list_sessions()
        assert len(sessions) == 2

    async def test_ordered_by_updated_at_descending(
        self, repo: SqliteChatRepositoryAdapter
    ) -> None:
        s1 = _make_session(session_id="s1", name="older")
        s2 = _make_session(session_id="s2", name="newer", updated_at=_LATER)
        await repo.create_session(s1)
        await repo.create_session(s2)

        sessions = await repo.list_sessions()
        assert sessions[0].name == "newer"

    async def test_returns_empty_tuple_when_no_sessions(
        self, repo: SqliteChatRepositoryAdapter
    ) -> None:
        sessions = await repo.list_sessions()
        assert sessions == ()

    async def test_message_count_reflected(
        self, repo: SqliteChatRepositoryAdapter
    ) -> None:
        session = _make_session()
        await repo.create_session(session)
        await repo.save_message(session.session_id, _make_message(message_id="m1"))
        await repo.save_message(session.session_id, _make_message(message_id="m2"))

        sessions = await repo.list_sessions()
        assert len(sessions[0].messages) == 2


class TestDeleteSession:
    """delete_session must remove session and all messages."""

    async def test_session_deleted(
        self, repo: SqliteChatRepositoryAdapter
    ) -> None:
        session = _make_session()
        await repo.create_session(session)
        await repo.save_message(session.session_id, _make_message())

        await repo.delete_session(session.session_id)

        result = await repo.load_session(session.session_id)
        assert result is None

    async def test_other_sessions_unaffected(
        self, repo: SqliteChatRepositoryAdapter
    ) -> None:
        s1 = _make_session(session_id="s1", name="keep")
        s2 = _make_session(session_id="s2", name="delete")
        await repo.create_session(s1)
        await repo.create_session(s2)

        await repo.delete_session("s2")

        sessions = await repo.list_sessions()
        assert len(sessions) == 1
        assert sessions[0].session_id == "s1"


class TestFindSessionByName:
    """find_session_by_name must do case-insensitive partial matching."""

    async def test_finds_exact_name(
        self, repo: SqliteChatRepositoryAdapter
    ) -> None:
        session = _make_session(name="quantum-research")
        await repo.create_session(session)

        result = await repo.find_session_by_name("quantum-research")
        assert result is not None
        assert result.name == "quantum-research"

    async def test_finds_partial_name(
        self, repo: SqliteChatRepositoryAdapter
    ) -> None:
        session = _make_session(name="quantum-research")
        await repo.create_session(session)

        result = await repo.find_session_by_name("quantum")
        assert result is not None

    async def test_case_insensitive(
        self, repo: SqliteChatRepositoryAdapter
    ) -> None:
        session = _make_session(name="Quantum-Research")
        await repo.create_session(session)

        result = await repo.find_session_by_name("quantum")
        assert result is not None

    async def test_returns_none_when_not_found(
        self, repo: SqliteChatRepositoryAdapter
    ) -> None:
        result = await repo.find_session_by_name("nonexistent")
        assert result is None

    async def test_loads_messages(
        self, repo: SqliteChatRepositoryAdapter
    ) -> None:
        session = _make_session(name="with-messages")
        await repo.create_session(session)
        await repo.save_message(session.session_id, _make_message())

        result = await repo.find_session_by_name("with-messages")
        assert result is not None
        assert len(result.messages) == 1


class TestClose:
    """close must be idempotent."""

    async def test_close_before_any_operation(self, tmp_path: Path) -> None:
        adapter = SqliteChatRepositoryAdapter(db_path=str(tmp_path / "test.db"))
        await adapter.close()

    async def test_double_close(self, tmp_path: Path) -> None:
        adapter = SqliteChatRepositoryAdapter(db_path=str(tmp_path / "test.db"))
        await adapter.create_session(_make_session())
        await adapter.close()
        await adapter.close()
