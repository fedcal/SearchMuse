"""Lightweight HTTP client for the Ollama REST API.

Provides model listing, pull-with-progress, reachability check, and
model existence verification. Uses httpx for synchronous HTTP so it
can be called directly from Typer CLI commands without an event loop.
"""

from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING, Any

import httpx

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

_DEFAULT_TIMEOUT: float = 3.0
_PULL_TIMEOUT: float = 600.0


@dataclasses.dataclass(frozen=True, slots=True)
class OllamaModel:
    """Immutable representation of an installed Ollama model."""

    name: str
    size_bytes: int
    modified_at: str


def is_reachable(base_url: str) -> bool:
    """Check whether the Ollama server is reachable.

    Args:
        base_url: Ollama server URL (e.g. ``http://localhost:11434``).

    Returns:
        True when the server responds to GET /api/tags within timeout.
    """
    try:
        response = httpx.get(f"{base_url}/api/tags", timeout=_DEFAULT_TIMEOUT)
        return response.status_code == 200
    except (httpx.HTTPError, OSError):
        return False


def list_models(base_url: str) -> tuple[OllamaModel, ...]:
    """Fetch the list of locally installed models.

    Args:
        base_url: Ollama server URL.

    Returns:
        An immutable tuple of :class:`OllamaModel` instances.

    Raises:
        httpx.HTTPStatusError: If the server returns a non-2xx status.
        httpx.HTTPError: On network errors.
    """
    response = httpx.get(f"{base_url}/api/tags", timeout=_DEFAULT_TIMEOUT)
    response.raise_for_status()
    data: dict[str, Any] = response.json()
    models_raw: list[dict[str, Any]] = data.get("models", [])
    return tuple(
        OllamaModel(
            name=m.get("name", ""),
            size_bytes=m.get("size", 0),
            modified_at=m.get("modified_at", ""),
        )
        for m in models_raw
    )


def model_exists(base_url: str, name: str) -> bool:
    """Check whether a model with the given name is installed.

    Performs a substring match so both ``"llama3"`` and
    ``"llama3:latest"`` are found.

    Args:
        base_url: Ollama server URL.
        name: Model name or prefix to search for.

    Returns:
        True when at least one installed model matches.
    """
    try:
        models = list_models(base_url)
    except (httpx.HTTPError, OSError):
        return False
    return any(name in m.name for m in models)


def pull_model(
    base_url: str,
    name: str,
    progress_callback: Callable[[int, int, str], None] | None = None,
) -> None:
    """Pull (download) a model from the Ollama registry with streaming progress.

    Args:
        base_url: Ollama server URL.
        name: Name of the model to pull (e.g. ``"llama3"``).
        progress_callback: Optional callback invoked for each progress chunk.
            Receives ``(completed_bytes, total_bytes, status_message)``.

    Raises:
        httpx.HTTPStatusError: If the server returns a non-2xx status.
        httpx.HTTPError: On network errors.
    """
    for chunk in _pull_stream(base_url, name):
        if progress_callback is not None:
            completed = chunk.get("completed", 0)
            total = chunk.get("total", 0)
            status = chunk.get("status", "")
            progress_callback(completed, total, status)


def _pull_stream(base_url: str, name: str) -> Iterator[dict[str, Any]]:
    """Yield parsed JSON chunks from the Ollama pull endpoint.

    Args:
        base_url: Ollama server URL.
        name: Model name to pull.

    Yields:
        Parsed JSON dicts from the streaming response.
    """
    import json

    with httpx.stream(
        "POST",
        f"{base_url}/api/pull",
        json={"name": name, "stream": True},
        timeout=httpx.Timeout(_PULL_TIMEOUT, connect=10.0),
    ) as response:
        response.raise_for_status()
        for line in response.iter_lines():
            stripped = line.strip()
            if stripped:
                yield json.loads(stripped)
