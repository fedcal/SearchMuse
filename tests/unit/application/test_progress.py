"""Unit tests for the progress callback system.

Tests cover:
- ProgressEvent immutability (frozen dataclass)
- ProgressEvent field defaults and explicit values
- NullProgress callable behaviour (no-op, no exception)
"""

from __future__ import annotations

import dataclasses

import pytest

from searchmuse.application.progress import NullProgress, ProgressEvent
from searchmuse.domain.enums import SearchPhase


class TestProgressEvent:
    """Tests for the frozen ProgressEvent dataclass."""

    def test_is_frozen(self) -> None:
        """ProgressEvent must not allow attribute mutation after creation."""
        event = ProgressEvent(phase=SearchPhase.SCRAPING, message="Fetching page")
        with pytest.raises((dataclasses.FrozenInstanceError, AttributeError)):
            event.message = "mutated"  # type: ignore[misc]

    def test_required_fields_stored_correctly(self) -> None:
        """phase and message are stored as supplied."""
        event = ProgressEvent(phase=SearchPhase.SYNTHESIZING, message="Building answer")
        assert event.phase == SearchPhase.SYNTHESIZING
        assert event.message == "Building answer"

    def test_iteration_defaults_to_zero(self) -> None:
        """iteration should default to 0 when not provided."""
        event = ProgressEvent(phase=SearchPhase.INITIALIZING, message="Starting")
        assert event.iteration == 0

    def test_detail_defaults_to_empty_string(self) -> None:
        """detail should default to an empty string when not provided."""
        event = ProgressEvent(phase=SearchPhase.INITIALIZING, message="Starting")
        assert event.detail == ""

    def test_explicit_iteration_and_detail(self) -> None:
        """Explicit iteration and detail values are stored correctly."""
        event = ProgressEvent(
            phase=SearchPhase.SCRAPING,
            message="Scraping URL",
            iteration=3,
            detail="https://example.com",
        )
        assert event.iteration == 3
        assert event.detail == "https://example.com"

    def test_all_search_phases_accepted(self) -> None:
        """ProgressEvent accepts every member of the SearchPhase enum."""
        for phase in SearchPhase:
            event = ProgressEvent(phase=phase, message="phase test")
            assert event.phase == phase

    def test_equality_based_on_values(self) -> None:
        """Two ProgressEvents with identical fields must compare equal."""
        event_a = ProgressEvent(phase=SearchPhase.COMPLETE, message="Done", iteration=2)
        event_b = ProgressEvent(phase=SearchPhase.COMPLETE, message="Done", iteration=2)
        assert event_a == event_b

    def test_inequality_on_differing_fields(self) -> None:
        """Two ProgressEvents that differ in any field must not compare equal."""
        event_a = ProgressEvent(phase=SearchPhase.COMPLETE, message="Done")
        event_b = ProgressEvent(phase=SearchPhase.FAILED, message="Done")
        assert event_a != event_b


class TestNullProgress:
    """Tests for the NullProgress no-op callback."""

    def test_call_does_not_raise_for_minimal_event(self) -> None:
        """NullProgress.__call__ must silently discard a minimal event."""
        null_progress = NullProgress()
        event = ProgressEvent(phase=SearchPhase.INITIALIZING, message="init")
        null_progress(event)  # must not raise

    def test_call_does_not_raise_for_full_event(self) -> None:
        """NullProgress.__call__ must silently discard a fully populated event."""
        null_progress = NullProgress()
        event = ProgressEvent(
            phase=SearchPhase.SCRAPING,
            message="Scraping",
            iteration=5,
            detail="https://example.org",
        )
        null_progress(event)  # must not raise

    def test_callable_multiple_times(self) -> None:
        """NullProgress can be invoked repeatedly without side effects."""
        null_progress = NullProgress()
        for phase in SearchPhase:
            event = ProgressEvent(phase=phase, message="tick")
            null_progress(event)  # must not raise on any iteration
