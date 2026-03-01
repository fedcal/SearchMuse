"""CLI layer: Typer application with Rich output."""

from __future__ import annotations

from pathlib import Path  # noqa: TC003 - Typer evaluates annotations at runtime

import typer

from searchmuse.version import __version__

app = typer.Typer(
    name="searchmuse",
    help="Intelligent web research powered by local LLMs.",
    no_args_is_help=False,
    invoke_without_command=True,
    add_completion=False,
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"SearchMuse v{__version__}")
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(
        False,
        "--version",
        "-V",
        help="Show version and exit.",
        callback=_version_callback,
        is_eager=True,
    ),
    config_path: Path | None = typer.Option(
        None, "--config", "-c", help="Path to custom config YAML",
    ),
    lang: str | None = typer.Option(
        None, "--lang", "-l", help="UI language: en, it, fr, de, es",
    ),
) -> None:
    """SearchMuse: Intelligent web research powered by local LLMs."""
    if lang is not None:
        import os
        os.environ["SEARCHMUSE_LOGGING_UILANGUAGE"] = lang

    if ctx.invoked_subcommand is None:
        from searchmuse.cli.interactive import InteractiveSession

        session = InteractiveSession(config_path=config_path)
        session.run()


@app.command("search")
def search_command(
    query: str = typer.Argument(..., help="The search query"),
    provider: str | None = typer.Option(
        None, "--provider", "-p", help="LLM provider: ollama, claude, openai, gemini",
    ),
    model: str | None = typer.Option(None, "--model", "-m", help="LLM model to use"),
    max_iterations: int | None = typer.Option(
        None, "--max-iterations", "-i", help="Maximum search iterations",
    ),
    output_format: str | None = typer.Option(
        None, "--format", "-f", help="Output format: markdown, json",
    ),
    config_path: Path | None = typer.Option(
        None, "--config", "-c", help="Path to custom config YAML",
    ),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress progress output"),
) -> None:
    """Execute an intelligent web search with LLM-powered analysis."""
    from searchmuse.cli.commands import run_search

    run_search(
        query,
        provider=provider,
        model=model,
        max_iterations=max_iterations,
        output_format=output_format,
        config_path=config_path,
        quiet=quiet,
    )


from searchmuse.cli.commands import config_app  # noqa: E402
from searchmuse.cli.ollama_commands import ollama_app  # noqa: E402

app.add_typer(config_app, name="config", help="Manage configuration")
app.add_typer(ollama_app, name="ollama", help="Manage Ollama models")
