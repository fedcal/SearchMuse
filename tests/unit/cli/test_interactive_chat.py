"""Unit tests for chat commands in the interactive REPL.

Tests the chat command handling in InteractiveSession using mock repositories.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

from searchmuse.cli.interactive import InteractiveSession, _extract_context
from searchmuse.domain.models import ChatMessage, ChatSession

_NOW = datetime(2024, 6, 1, 12, 0, 0, tzinfo=UTC)


def _make_session(
    *,
    session_id: str = "sess-001",
    name: str = "test-chat",
    messages: tuple[ChatMessage, ...] = (),
) -> ChatSession:
    return ChatSession(
        session_id=session_id,
        name=name,
        messages=messages,
        created_at=_NOW,
        updated_at=_NOW,
    )


def _make_message(
    *,
    message_id: str = "msg-001",
    role: str = "user",
    content: str = "test content",
) -> ChatMessage:
    return ChatMessage(
        message_id=message_id,
        role=role,
        content=content,
        created_at=_NOW,
    )


class TestExtractContext:
    """_extract_context must pair user/assistant messages."""

    def test_empty_session(self) -> None:
        session = _make_session()
        result = _extract_context(session)
        assert result == []

    def test_single_pair(self) -> None:
        messages = (
            _make_message(message_id="m1", role="user", content="query1"),
            _make_message(message_id="m2", role="assistant", content="answer1"),
        )
        session = _make_session(messages=messages)
        result = _extract_context(session)
        assert len(result) == 1
        assert result[0] == ("query1", "answer1")

    def test_multiple_pairs(self) -> None:
        messages = (
            _make_message(message_id="m1", role="user", content="q1"),
            _make_message(message_id="m2", role="assistant", content="a1"),
            _make_message(message_id="m3", role="user", content="q2"),
            _make_message(message_id="m4", role="assistant", content="a2"),
        )
        session = _make_session(messages=messages)
        result = _extract_context(session)
        assert len(result) == 2
        assert result[0] == ("q1", "a1")
        assert result[1] == ("q2", "a2")

    def test_unpaired_user_message_skipped(self) -> None:
        messages = (
            _make_message(message_id="m1", role="user", content="q1"),
            _make_message(message_id="m2", role="assistant", content="a1"),
            _make_message(message_id="m3", role="user", content="q2"),
        )
        session = _make_session(messages=messages)
        result = _extract_context(session)
        assert len(result) == 1


class TestCmdNew:
    """The 'new' command must clear current chat state."""

    def test_new_clears_chat(self) -> None:
        session = InteractiveSession()
        session._current_chat = _make_session()
        session._chat_context = [("q", "a")]

        session._cmd_new()

        assert session._current_chat is None
        assert session._chat_context == []


class TestCmdContext:
    """The 'context' command must display current context info."""

    def test_context_with_no_context(self) -> None:
        session = InteractiveSession()
        session._console = MagicMock()
        session._cmd_context()
        session._console.print.assert_called()

    def test_context_with_entries(self) -> None:
        session = InteractiveSession()
        session._console = MagicMock()
        session._chat_context = [("q1", "a1"), ("q2", "a2")]
        session._cmd_context()
        # Verify multiple print calls were made
        assert session._console.print.call_count >= 3


class TestChatCommandRouting:
    """Chat commands must be properly recognized and routed."""

    def test_chats_command_recognized(self) -> None:
        session = InteractiveSession()
        session._console = MagicMock()
        with (
            patch.object(session, "_cmd_chats", new_callable=AsyncMock),
            patch("searchmuse.cli.interactive.asyncio") as mock_asyncio,
        ):
            mock_asyncio.run = MagicMock(side_effect=lambda coro: None)
            session._handle_chat_command("chats", None)

    def test_new_command_recognized(self) -> None:
        session = InteractiveSession()
        session._console = MagicMock()
        with patch.object(session, "_cmd_new") as mock:
            session._handle_chat_command("new", None)
            mock.assert_called_once()

    def test_context_command_recognized(self) -> None:
        session = InteractiveSession()
        session._console = MagicMock()
        with patch.object(session, "_cmd_context") as mock:
            session._handle_chat_command("context", None)
            mock.assert_called_once()

    def test_rename_without_arg_prints_usage(self) -> None:
        session = InteractiveSession()
        session._console = MagicMock()
        session._handle_chat_command("rename", None)
        session._console.print.assert_called_once()
        assert "Usage" in session._console.print.call_args[0][0]

    def test_delete_without_arg_prints_usage(self) -> None:
        session = InteractiveSession()
        session._console = MagicMock()
        session._handle_chat_command("delete", None)
        session._console.print.assert_called_once()
        assert "Usage" in session._console.print.call_args[0][0]

    def test_save_routes_to_cmd_save(self) -> None:
        session = InteractiveSession()
        session._console = MagicMock()
        with (
            patch.object(session, "_cmd_save", new_callable=AsyncMock),
            patch("searchmuse.cli.interactive.asyncio") as mock_asyncio,
        ):
            mock_asyncio.run = MagicMock(side_effect=lambda coro: None)
            session._handle_chat_command("save my-chat", None)
            mock_asyncio.run.assert_called_once()

    def test_load_routes_to_cmd_load(self) -> None:
        session = InteractiveSession()
        session._console = MagicMock()
        with (
            patch.object(session, "_cmd_load", new_callable=AsyncMock),
            patch("searchmuse.cli.interactive.asyncio") as mock_asyncio,
        ):
            mock_asyncio.run = MagicMock(side_effect=lambda coro: None)
            session._handle_chat_command("load some-id", None)
            mock_asyncio.run.assert_called_once()

    def test_rename_with_arg_routes_to_cmd_rename(self) -> None:
        session = InteractiveSession()
        session._console = MagicMock()
        with (
            patch.object(session, "_cmd_rename", new_callable=AsyncMock),
            patch("searchmuse.cli.interactive.asyncio") as mock_asyncio,
        ):
            mock_asyncio.run = MagicMock(side_effect=lambda coro: None)
            session._handle_chat_command("rename new-name", None)
            mock_asyncio.run.assert_called_once()

    def test_delete_with_arg_routes_to_cmd_delete(self) -> None:
        session = InteractiveSession()
        session._console = MagicMock()
        with (
            patch.object(session, "_cmd_delete", new_callable=AsyncMock),
            patch("searchmuse.cli.interactive.asyncio") as mock_asyncio,
        ):
            mock_asyncio.run = MagicMock(side_effect=lambda coro: None)
            session._handle_chat_command("delete chat-name", None)
            mock_asyncio.run.assert_called_once()


def _make_config(db_path: str = "/tmp/test.db") -> MagicMock:
    """Build a minimal mock SearchMuseConfig with storage.db_path set."""
    config = MagicMock()
    config.storage.db_path = db_path
    config.llm.base_url = "http://localhost:11434"
    config.llm.model = "llama3"
    return config


class TestGetChatRepo:
    """_get_chat_repo builds a repository or returns None on missing config."""

    def test_none_config_returns_none(self) -> None:
        session = InteractiveSession()
        session._console = MagicMock()
        assert session._get_chat_repo(None) is None
        session._console.print.assert_called_once()

    def test_builds_repo_with_db_path(self) -> None:
        session = InteractiveSession()
        config = _make_config(db_path="/tmp/searchmuse.db")
        with patch(
            "searchmuse.adapters.repositories.sqlite_chat_repository.SqliteChatRepositoryAdapter"
        ) as mock_repo_cls:
            session._get_chat_repo(config)
            mock_repo_cls.assert_called_once()
            assert "searchmuse.db" in mock_repo_cls.call_args.kwargs["db_path"]


class TestCmdChatsAsync:
    """_cmd_chats lists saved sessions or shows empty notice."""

    async def test_no_repo_returns_silently(self) -> None:
        session = InteractiveSession()
        session._console = MagicMock()
        with patch.object(session, "_get_chat_repo", return_value=None):
            await session._cmd_chats(None)

    async def test_empty_sessions_prints_empty_message(self) -> None:
        session = InteractiveSession()
        session._console = MagicMock()
        repo = MagicMock()
        repo.list_sessions = AsyncMock(return_value=[])
        repo.close = AsyncMock()
        with patch.object(session, "_get_chat_repo", return_value=repo):
            await session._cmd_chats(_make_config())
        repo.list_sessions.assert_awaited_once()
        repo.close.assert_awaited_once()
        session._console.print.assert_called_once()

    async def test_populated_sessions_prints_table(self) -> None:
        session = InteractiveSession()
        session._console = MagicMock()
        sessions = [
            _make_session(session_id="abcd1234efgh", name="chat-a"),
            _make_session(session_id="xyz9876kkkk", name="chat-b"),
        ]
        repo = MagicMock()
        repo.list_sessions = AsyncMock(return_value=sessions)
        repo.close = AsyncMock()
        with patch.object(session, "_get_chat_repo", return_value=repo):
            await session._cmd_chats(_make_config())
        repo.close.assert_awaited_once()
        session._console.print.assert_called_once()


class TestCmdSaveAsync:
    """_cmd_save updates the session name or warns if no chat is active."""

    async def test_no_current_chat_warns(self) -> None:
        session = InteractiveSession()
        session._console = MagicMock()
        await session._cmd_save("foo", _make_config())
        session._console.print.assert_called_once()

    async def test_no_repo_returns_silently(self) -> None:
        session = InteractiveSession()
        session._console = MagicMock()
        session._current_chat = _make_session()
        with patch.object(session, "_get_chat_repo", return_value=None):
            await session._cmd_save("foo", None)

    async def test_save_with_name_updates_repo(self) -> None:
        session = InteractiveSession()
        session._console = MagicMock()
        session._current_chat = _make_session(name="old-name")
        repo = MagicMock()
        repo.update_session_name = AsyncMock()
        repo.close = AsyncMock()
        with patch.object(session, "_get_chat_repo", return_value=repo):
            await session._cmd_save("new-name", _make_config())
        repo.update_session_name.assert_awaited_once()
        assert session._current_chat is not None
        assert session._current_chat.name == "new-name"

    async def test_save_without_name_uses_existing(self) -> None:
        session = InteractiveSession()
        session._console = MagicMock()
        session._current_chat = _make_session(name="keep-me")
        repo = MagicMock()
        repo.update_session_name = AsyncMock()
        repo.close = AsyncMock()
        with patch.object(session, "_get_chat_repo", return_value=repo):
            await session._cmd_save("", _make_config())
        assert session._current_chat is not None
        assert session._current_chat.name == "keep-me"


class TestCmdLoadAsync:
    """_cmd_load loads a session by id or by name, with not-found handling."""

    async def test_no_repo_returns_silently(self) -> None:
        session = InteractiveSession()
        session._console = MagicMock()
        with patch.object(session, "_get_chat_repo", return_value=None):
            await session._cmd_load("anything", None)

    async def test_not_found_prints_warning(self) -> None:
        session = InteractiveSession()
        session._console = MagicMock()
        repo = MagicMock()
        repo.load_session = AsyncMock(return_value=None)
        repo.find_session_by_name = AsyncMock(return_value=None)
        repo.close = AsyncMock()
        with patch.object(session, "_get_chat_repo", return_value=repo):
            await session._cmd_load("missing", _make_config())
        repo.load_session.assert_awaited_once_with("missing")
        repo.find_session_by_name.assert_awaited_once_with("missing")
        session._console.print.assert_called_once()

    async def test_found_by_id_sets_current_chat(self) -> None:
        session = InteractiveSession()
        session._console = MagicMock()
        loaded = _make_session(name="loaded-chat")
        repo = MagicMock()
        repo.load_session = AsyncMock(return_value=loaded)
        repo.close = AsyncMock()
        with patch.object(session, "_get_chat_repo", return_value=repo):
            await session._cmd_load("sess-001", _make_config())
        assert session._current_chat == loaded
        assert session._chat_context == []

    async def test_found_by_name_when_id_missing(self) -> None:
        session = InteractiveSession()
        session._console = MagicMock()
        loaded = _make_session(name="by-name")
        repo = MagicMock()
        repo.load_session = AsyncMock(return_value=None)
        repo.find_session_by_name = AsyncMock(return_value=loaded)
        repo.close = AsyncMock()
        with patch.object(session, "_get_chat_repo", return_value=repo):
            await session._cmd_load("by-name", _make_config())
        assert session._current_chat == loaded


class TestCmdRenameAsync:
    """_cmd_rename updates the current chat name."""

    async def test_no_current_chat_warns(self) -> None:
        session = InteractiveSession()
        session._console = MagicMock()
        await session._cmd_rename("new-name", _make_config())
        session._console.print.assert_called_once()

    async def test_no_repo_returns_silently(self) -> None:
        session = InteractiveSession()
        session._console = MagicMock()
        session._current_chat = _make_session()
        with patch.object(session, "_get_chat_repo", return_value=None):
            await session._cmd_rename("x", None)

    async def test_rename_updates_session(self) -> None:
        session = InteractiveSession()
        session._console = MagicMock()
        session._current_chat = _make_session(name="before")
        repo = MagicMock()
        repo.update_session_name = AsyncMock()
        repo.close = AsyncMock()
        with patch.object(session, "_get_chat_repo", return_value=repo):
            await session._cmd_rename("after", _make_config())
        assert session._current_chat is not None
        assert session._current_chat.name == "after"


class TestCmdDeleteAsync:
    """_cmd_delete removes a saved session and clears current state if affected."""

    async def test_no_repo_returns_silently(self) -> None:
        session = InteractiveSession()
        session._console = MagicMock()
        with patch.object(session, "_get_chat_repo", return_value=None):
            await session._cmd_delete("x", None)

    async def test_not_found_prints_warning(self) -> None:
        session = InteractiveSession()
        session._console = MagicMock()
        repo = MagicMock()
        repo.load_session = AsyncMock(return_value=None)
        repo.find_session_by_name = AsyncMock(return_value=None)
        repo.close = AsyncMock()
        with patch.object(session, "_get_chat_repo", return_value=repo):
            await session._cmd_delete("missing", _make_config())
        session._console.print.assert_called_once()

    async def test_delete_clears_current_when_match(self) -> None:
        session = InteractiveSession()
        session._console = MagicMock()
        target = _make_session(session_id="del-001", name="to-delete")
        session._current_chat = target
        session._chat_context = [("q", "a")]
        repo = MagicMock()
        repo.load_session = AsyncMock(return_value=target)
        repo.delete_session = AsyncMock()
        repo.close = AsyncMock()
        with patch.object(session, "_get_chat_repo", return_value=repo):
            await session._cmd_delete("del-001", _make_config())
        repo.delete_session.assert_awaited_once_with("del-001")
        assert session._current_chat is None
        assert session._chat_context == []

    async def test_delete_keeps_current_when_different(self) -> None:
        session = InteractiveSession()
        session._console = MagicMock()
        current = _make_session(session_id="keep-001", name="keep")
        target = _make_session(session_id="del-001", name="delete")
        session._current_chat = current
        repo = MagicMock()
        repo.load_session = AsyncMock(return_value=target)
        repo.delete_session = AsyncMock()
        repo.close = AsyncMock()
        with patch.object(session, "_get_chat_repo", return_value=repo):
            await session._cmd_delete("del-001", _make_config())
        assert session._current_chat == current


class TestSaveChatMessagesAsync:
    """_save_chat_messages persists user/assistant messages."""

    async def test_no_repo_returns_silently(self) -> None:
        session = InteractiveSession()
        result = MagicMock()
        result.synthesis = "answer"
        with patch.object(session, "_get_chat_repo", return_value=None):
            await session._save_chat_messages("query", result, None)

    async def test_auto_creates_session_on_first_call(self) -> None:
        session = InteractiveSession()
        session._console = MagicMock()
        result = MagicMock()
        result.synthesis = "answer"
        repo = MagicMock()
        repo.create_session = AsyncMock()
        repo.save_message = AsyncMock()
        repo.update_session_timestamp = AsyncMock()
        repo.close = AsyncMock()
        with patch.object(session, "_get_chat_repo", return_value=repo):
            await session._save_chat_messages("my query", result, _make_config())
        repo.create_session.assert_awaited_once()
        assert repo.save_message.await_count == 2
        assert session._current_chat is not None
        assert session._current_chat.name == "my query"
        assert session._chat_context == [("my query", "answer")]

    async def test_appends_to_existing_session(self) -> None:
        session = InteractiveSession()
        session._console = MagicMock()
        session._current_chat = _make_session(session_id="exist-001")
        result = MagicMock()
        result.synthesis = "answer"
        repo = MagicMock()
        repo.create_session = AsyncMock()
        repo.save_message = AsyncMock()
        repo.update_session_timestamp = AsyncMock()
        repo.close = AsyncMock()
        with patch.object(session, "_get_chat_repo", return_value=repo):
            await session._save_chat_messages("follow up", result, _make_config())
        repo.create_session.assert_not_called()
        assert repo.save_message.await_count == 2
        repo.update_session_timestamp.assert_awaited_once_with("exist-001")
