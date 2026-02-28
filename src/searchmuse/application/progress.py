"""Progress callback system for decoupled progress reporting.

Provides a simple event-based mechanism for the orchestrator to emit
progress updates without depending on any specific UI framework.
"""

from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from searchmuse.domain.enums import SearchPhase


@dataclasses.dataclass(frozen=True, slots=True)
class ProgressEvent:
    """An immutable progress event emitted by the orchestrator.

    Attributes:
        phase: Current search phase.
        message: Human-readable description of what is happening.
        iteration: Current iteration number (0 before first iteration).
        detail: Optional extra detail (e.g. URL being scraped).
    """

    phase: SearchPhase
    message: str
    iteration: int = 0
    detail: str = ""


class ProgressCallback(Protocol):
    """Protocol for receiving progress events."""

    def __call__(self, event: ProgressEvent) -> None:
        """Handle a progress event.

        Args:
            event: The progress event to process.
        """
        ...


class NullProgress:
    """No-op progress callback that discards all events."""

    def __call__(self, event: ProgressEvent) -> None:
        """Discard the event."""
