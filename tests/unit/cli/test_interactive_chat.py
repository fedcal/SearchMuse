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
