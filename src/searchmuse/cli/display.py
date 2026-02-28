"""Rich terminal display helpers for SearchMuse CLI.

Provides a banner, progress spinner, result panels, and error formatting
without leaking Rich dependencies into the application layer.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from searchmuse.domain.enums import SearchPhase
from searchmuse.version import __version__

if TYPE_CHECKING:
    from rich.status import Status

    from searchmuse.application.progress import ProgressCallback, ProgressEvent
    from searchmuse.domain.models import SearchResult
    from searchmuse.infrastructure.config import SearchMuseConfig

_PHASE_LABELS: dict[SearchPhase, str] = {
    SearchPhase.INITIALIZING: "Initializing",
    SearchPhase.STRATEGIZING: "Strategizing",
    SearchPhase.SCRAPING: "Scraping",
    SearchPhase.EXTRACTING: "Extracting",
    SearchPhase.ASSESSING: "Assessing",
    SearchPhase.SYNTHESIZING: "Synthesizing",
    SearchPhase.COMPLETE: "Complete",
    SearchPhase.FAILED: "Failed",
}

_PHASE_COLORS: dict[SearchPhase, str] = {
    SearchPhase.INITIALIZING: "blue",
    SearchPhase.STRATEGIZING: "cyan",
    SearchPhase.SCRAPING: "yellow",
    SearchPhase.EXTRACTING: "magenta",
    SearchPhase.ASSESSING: "green",
    SearchPhase.SYNTHESIZING: "bright_cyan",
    SearchPhase.COMPLETE: "bold green",
    SearchPhase.FAILED: "bold red",
}


_MASCOT_ART: tuple[str, ...] = (
    "      [cyan]🔍📚[/]",
    "   .--------.",
    "   | [cyan]◉[/]    [cyan]◉[/] |",
    "   |  [cyan]‿‿‿‿[/]  |",
    "   |  [bold]MUSE[/]  |",
    "   '--------'",
)

_MAX_PATH_LENGTH = 40


def _abbreviate_path(path: Path, max_length: int = _MAX_PATH_LENGTH) -> str:
    """Shorten a path for display, keeping root and tail."""
    text = str(path)
    if len(text) <= max_length:
        return text
    parts = path.parts
    if len(parts) <= 3:
        return text
    tail = str(Path(*parts[-2:]))
    return f"{parts[0]}/.../{tail}"


class Display:
    """Rich-based terminal display for SearchMuse."""

    def __init__(self, *, quiet: bool = False) -> None:
        self._console = Console(stderr=True)
        self._output = Console()
        self._quiet = quiet
        self._status: Status | None = None

    def show_banner(self, config: SearchMuseConfig | None = None) -> None:
        """Print the SearchMuse welcome banner with two-column layout."""
        if self._quiet:
            return

        table = Table(
            show_header=False,
            show_edge=False,
            show_lines=False,
            padding=(0, 2),
            expand=True,
        )
        table.add_column(ratio=1)
        table.add_column(ratio=1)

        left = self._build_banner_left(config)
        right = self._build_banner_right(config)
        table.add_row(left, right)

        panel = Panel(
            table,
            border_style="cyan",
            title=f"SearchMuse v{__version__}",
            title_align="left",
            padding=(1, 2),
        )
        self._console.print(panel)

    def _build_banner_left(self, config: SearchMuseConfig | None) -> Text:
        """Build the left column: welcome message, mascot, provider info."""
        parts: list[str] = [
            "[bold cyan]Welcome to SearchMuse![/]",
            "",
        ]
        parts.extend(_MASCOT_ART)
        parts.append("")

        if config is not None:
            parts.append(
                f"[dim]{config.llm.provider} · {config.llm.model}[/]"
            )

        cwd = _abbreviate_path(Path.cwd())
        parts.append(f"[dim]{cwd}[/]")

        return Text.from_markup("\n".join(parts))

    def _build_banner_right(self, config: SearchMuseConfig | None) -> Text:
        """Build the right column: tips and provider status."""
        parts: list[str] = [
            "[bold yellow]Tips for getting started[/]",
            '  searchmuse search [cyan]"your query"[/]',
            "  Use [bold]-p claude[/] to switch provider",
            "  searchmuse config check",
            "",
        ]

        if config is not None:
            parts.extend(self._build_provider_status(config))

        return Text.from_markup("\n".join(parts))

    @staticmethod
    def _build_provider_status(config: SearchMuseConfig) -> list[str]:
        """Build provider status lines showing availability of each provider."""
        from searchmuse.adapters.llm._defaults import PROVIDER_DEFAULTS
        from searchmuse.infrastructure.api_key_resolver import resolve_api_key

        lines: list[str] = ["[bold yellow]Provider status[/]"]

        for name, defaults in PROVIDER_DEFAULTS.items():
            is_active = name == config.llm.provider
            model = config.llm.model if is_active else defaults.model

            if not defaults.requires_api_key:
                marker = "[green]✓[/]"
                lines.append(f"  {marker} {name} · {model}")
            else:
                config_key = (
                    config.llm.api_key if is_active else None
                )
                has_key = resolve_api_key(name, config_key) is not None
                if has_key:
                    lines.append(f"  [green]✓[/] {name} · {model}")
                else:
                    lines.append(
                        f"  [red]✗[/] {name} · [dim](no API key)[/]"
                    )

        return lines

    def start_progress(self) -> None:
        """Start the progress spinner."""
        if self._quiet:
            return
        self._status = self._console.status(
            "Starting...",
            spinner="dots",
        )
        self._status.start()

    def stop_progress(self) -> None:
        """Stop the progress spinner."""
        if self._status is not None:
            self._status.stop()
            self._status = None

    def update_progress(self, event: ProgressEvent) -> None:
        """Update the progress spinner with a new event."""
        if self._quiet:
            return

        label = _PHASE_LABELS.get(event.phase, str(event.phase))
        color = _PHASE_COLORS.get(event.phase, "white")

        message = f"[{color}]{label}[/] {event.message}"
        if event.detail:
            message += f" [dim]({event.detail})[/]"

        if self._status is not None:
            self._status.update(message)
        else:
            self._console.print(message)

    def show_result(self, result: SearchResult, rendered: str) -> None:
        """Display the final search result."""
        self.stop_progress()

        self._output.print()
        self._output.print(Markdown(rendered))
        self._output.print()

    def show_result_raw(self, rendered: str) -> None:
        """Print raw rendered output (for non-markdown formats)."""
        self.stop_progress()
        self._output.print(rendered)

    def show_error(self, title: str, message: str) -> None:
        """Display an error panel."""
        self.stop_progress()
        panel = Panel(
            f"[bold]{title}[/]\n\n{message}",
            border_style="red",
            title="Error",
            padding=(1, 2),
        )
        self._console.print(panel)

    def show_info(self, message: str) -> None:
        """Print an informational message."""
        if not self._quiet:
            self._console.print(f"[dim]{message}[/]")

    def show_config(self, config_text: str) -> None:
        """Display configuration in a panel."""
        panel = Panel(
            config_text,
            border_style="cyan",
            title="Configuration",
            padding=(1, 2),
        )
        self._console.print(panel)

    def show_check_result(self, *, ok: bool, service: str, detail: str) -> None:
        """Display a service check result."""
        icon = "[green]OK[/]" if ok else "[red]FAIL[/]"
        self._console.print(f"  {icon} {service}: {detail}")

    def make_progress_callback(self) -> ProgressCallback:
        """Create a progress callback bound to this display."""
        return self.update_progress
