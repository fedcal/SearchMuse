"""Unit tests for ChatMessage and ChatSession domain models.

Verifies frozen immutability, with_* methods, and field access.
"""

from __future__ import annotations

import dataclasses
from datetime import UTC, datetime

import pytest

from searchmuse.domain.models import ChatMessage, ChatSession

_NOW = datetime(2024, 6, 1, 12, 0, 0, tzinfo=UTC)
_LATER = datetime(2024, 6, 1, 13, 0, 0, tzinfo=UTC)


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


def _make_session(
    *,
    session_id: str = "sess-001",
    name: str = "test-chat",
    messages: tuple[ChatMessage, ...] = (),
    created_at: datetime = _NOW,
    updated_at: datetime = _NOW,
) -> ChatSession:
    return ChatSession(
        session_id=session_id,
        name=name,
        messages=messages,
        created_at=created_at,
        updated_at=updated_at,
    )


class TestChatMessageFrozen:
    """ChatMessage must be frozen and raise on attribute assignment."""

    def test_message_is_frozen(self) -> None:
        msg = _make_message()
        with pytest.raises(dataclasses.FrozenInstanceError):
            msg.content = "mutated"  # type: ignore[misc]

    def test_message_fields_accessible(self) -> None:
        msg = _make_message(
            message_id="abc",
            role="assistant",
            content="Answer text",
            result_json='{"key": "value"}',
        )
        assert msg.message_id == "abc"
        assert msg.role == "assistant"
        assert msg.content == "Answer text"
        assert msg.result_json == '{"key": "value"}'
        assert msg.created_at == _NOW

    def test_message_default_result_json(self) -> None:
        msg = _make_message()
        assert msg.result_json == ""


class TestChatSessionFrozen:
    """ChatSession must be frozen and raise on attribute assignment."""

    def test_session_is_frozen(self) -> None:
        session = _make_session()
        with pytest.raises(dataclasses.FrozenInstanceError):
            session.name = "mutated"  # type: ignore[misc]

    def test_session_fields_accessible(self) -> None:
        session = _make_session(
            session_id="s1",
            name="my-chat",
        )
        assert session.session_id == "s1"
        assert session.name == "my-chat"
        assert session.messages == ()
        assert session.created_at == _NOW
        assert session.updated_at == _NOW


class TestChatSessionWithMessage:
    """with_message must return a new instance with the message appended."""

    def test_returns_new_object(self) -> None:
        session = _make_session()
        msg = _make_message()
        updated = session.with_message(msg)
        assert updated is not session

    def test_original_unchanged(self) -> None:
        session = _make_session()
        msg = _make_message()
        _ = session.with_message(msg)
        assert session.messages == ()

    def test_appends_message(self) -> None:
        session = _make_session()
        msg = _make_message()
        updated = session.with_message(msg)
        assert len(updated.messages) == 1
        assert updated.messages[0] is msg

    def test_updates_timestamp(self) -> None:
        session = _make_session()
        msg = _make_message(created_at=_LATER)
        updated = session.with_message(msg)
        assert updated.updated_at == _LATER

    def test_accumulates_messages(self) -> None:
        session = _make_session()
        msg1 = _make_message(message_id="m1")
        msg2 = _make_message(message_id="m2", created_at=_LATER)
        updated = session.with_message(msg1).with_message(msg2)
        assert len(updated.messages) == 2


class TestChatSessionWithName:
    """with_name must return a new instance with the name changed."""

    def test_returns_new_object(self) -> None:
        session = _make_session()
        updated = session.with_name("renamed", _LATER)
        assert updated is not session

    def test_original_unchanged(self) -> None:
        session = _make_session(name="original")
        _ = session.with_name("renamed", _LATER)
        assert session.name == "original"

    def test_sets_name(self) -> None:
        session = _make_session()
        updated = session.with_name("new-name", _LATER)
        assert updated.name == "new-name"

    def test_updates_timestamp(self) -> None:
        session = _make_session()
        updated = session.with_name("new-name", _LATER)
        assert updated.updated_at == _LATER
