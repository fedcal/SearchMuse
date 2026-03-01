"""Typer subcommands for managing Ollama models.

Provides ``list``, ``pull``, and ``select`` commands under the
``searchmuse ollama`` subcommand group.
"""

from __future__ import annotations

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)
from rich.table import Table

from searchmuse.infrastructure.config import load_config
from searchmuse.infrastructure.i18n import t

ollama_app = typer.Typer(help="Manage Ollama models")

_console = Console(stderr=True)

_DEFAULT_BASE_URL = "http://localhost:11434"


def _get_base_url() -> str:
    """Resolve the Ollama base URL from config, falling back to default."""
    try:
        config = load_config(None)
        return config.llm.base_url
    except Exception:
        return _DEFAULT_BASE_URL


@ollama_app.command("list")
def ollama_list() -> None:
    """List locally installed Ollama models."""
    from searchmuse.infrastructure.ollama_client import is_reachable, list_models

    base_url = _get_base_url()

    if not is_reachable(base_url):
        _console.print(
            Panel(
                f"{t('ollama_unreachable', url=base_url)}\n\n"
                f"[cyan]{t('ollama_start_hint')}[/]",
                border_style="red",
                title=t("ollama_conn_title"),
            )
        )
        raise typer.Exit(code=1)

    try:
        models = list_models(base_url)
    except Exception as exc:
        _console.print(f"[red]{t('error_fetching_models', error=exc)}[/]")
        raise typer.Exit(code=1) from exc

    if not models:
        _console.print(f"[yellow]{t('no_models_installed')}[/] {t('pull_hint')}")
        return

    table = Table(title="Ollama Models", border_style="cyan")
    table.add_column("Model", style="bold cyan")
    table.add_column("Size", justify="right")
    table.add_column("Modified", style="dim")

    for model in models:
        size = _format_size(model.size_bytes)
        modified = _format_date(model.modified_at)
        table.add_row(model.name, size, modified)

    _console.print(table)


@ollama_app.command("pull")
def ollama_pull(
    model: str = typer.Argument(..., help="Model name to pull (e.g. llama3, mistral)"),
) -> None:
    """Download an Ollama model with progress reporting."""
    from searchmuse.infrastructure.ollama_client import is_reachable, pull_model

    base_url = _get_base_url()

    if not is_reachable(base_url):
        _console.print(f"[red]{t('ollama_unreachable', url=base_url)}[/]")
        raise typer.Exit(code=1)

    _console.print(t("pulling_model", model=model))

    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
        console=_console,
    )

    task_id = progress.add_task(f"Pulling {model}", total=None)
    last_status = ""

    def _on_progress(completed: int, total: int, status: str) -> None:
        nonlocal last_status
        if total > 0:
            progress.update(task_id, total=total, completed=completed)
        if status != last_status:
            progress.update(task_id, description=status)
            last_status = status

    try:
        with progress:
            pull_model(base_url, model, progress_callback=_on_progress)
        _console.print(f"\n[green]{t('pull_success', model=model)}[/]")
    except Exception as exc:
        _console.print(f"\n[red]{t('pull_failed', error=exc)}[/]")
        raise typer.Exit(code=1) from exc


@ollama_app.command("select")
def ollama_select(
    model: str = typer.Argument(..., help="Model name to select for SearchMuse"),
) -> None:
    """Verify an Ollama model is installed and show how to configure it."""
    from searchmuse.infrastructure.ollama_client import is_reachable, model_exists

    base_url = _get_base_url()

    if not is_reachable(base_url):
        _console.print(f"[red]{t('ollama_unreachable', url=base_url)}[/]")
        raise typer.Exit(code=1)

    if not model_exists(base_url, model):
        _console.print(
            f"[yellow]{t('model_not_installed', model=model)}[/]\n"
            f"{t('model_pull_first', model=model)}"
        )
        raise typer.Exit(code=1)

    _console.print(f"[green]{t('model_available', model=model)}[/]\n")
    _console.print(t("model_env_hint"))
    _console.print(f"  [cyan]export SEARCHMUSE_LLM_MODEL={model}[/]\n")
    _console.print(t("model_config_hint"))
    _console.print(f"  [cyan]llm:\\n    model: {model}[/]")


def _format_size(size_bytes: int) -> str:
    """Format a byte count into a human-readable size string."""
    if size_bytes <= 0:
        return "—"
    units = ("B", "KB", "MB", "GB", "TB")
    value = float(size_bytes)
    for unit in units:
        if value < 1024:
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} PB"


def _format_date(iso_string: str) -> str:
    """Format an ISO datetime string into a short display form."""
    if not iso_string:
        return "—"
    try:
        # Ollama returns ISO 8601 with timezone; take just the date part
        return iso_string[:10]
    except (ValueError, IndexError):
        return iso_string
