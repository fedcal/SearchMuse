"""Typer CLI commands for SearchMuse.

Defines the search runner and config subcommands.
"""

from __future__ import annotations

import asyncio
import contextlib
from pathlib import Path
from typing import TYPE_CHECKING

import typer

from searchmuse.cli.display import Display
from searchmuse.domain.errors import (
    ConfigurationError,
    LLMAuthenticationError,
    LLMConnectionError,
    SearchMuseError,
    ValidationError,
)

if TYPE_CHECKING:
    from searchmuse.cli.container import Container
    from searchmuse.domain.models import SearchResult

config_app = typer.Typer(help="Configuration commands")


def run_search(
    query: str,
    *,
    provider: str | None,
    model: str | None,
    max_iterations: int | None,
    output_format: str | None,
    config_path: Path | None,
    quiet: bool,
) -> None:
    """Execute a search query (sync wrapper for async orchestrator)."""
    display = Display(quiet=quiet)

    import os

    if provider is not None:
        os.environ["SEARCHMUSE_LLM_PROVIDER"] = provider
    if model is not None:
        os.environ["SEARCHMUSE_LLM_MODEL"] = model
    if max_iterations is not None:
        os.environ["SEARCHMUSE_SEARCH_MAXITERATIONS"] = str(max_iterations)

    # Load config early so the banner can display provider status.
    from searchmuse.infrastructure.config import SearchMuseConfig, load_config

    banner_config: SearchMuseConfig | None = None
    with contextlib.suppress(Exception):
        banner_config = load_config(config_path)

    display.show_banner(banner_config)

    try:
        display.start_progress()

        from searchmuse.cli.container import build_container

        container = build_container(
            config_path=config_path,
            progress=display.make_progress_callback(),
        )

        result = asyncio.run(_async_search(container, query))

        rendered = container.renderer.render(result)

        if output_format == "json":
            import json

            json_data = {
                "session_id": result.session_id,
                "query": result.query.normalized_text,
                "synthesis": result.synthesis,
                "citations": [
                    {"index": c.index, "text": c.formatted_text, "url": c.url}
                    for c in result.citations
                ],
                "total_sources": result.total_sources_found,
                "iterations": result.iterations_performed,
                "duration_seconds": result.duration_seconds,
            }
            display.stop_progress()
            typer.echo(json.dumps(json_data, indent=2, ensure_ascii=False))
        else:
            display.show_result(result, rendered)

    except ValidationError as exc:
        display.show_error("Validation Error", str(exc))
        raise typer.Exit(code=1) from exc
    except LLMAuthenticationError as exc:
        display.show_error(
            "LLM Authentication Error",
            f"{exc}\n\nCheck your API key: searchmuse config set-key <provider> <key>",
        )
        raise typer.Exit(code=1) from exc
    except LLMConnectionError as exc:
        display.show_error(
            "LLM Connection Error",
            f"{exc}\n\nMake sure the LLM service is available.",
        )
        raise typer.Exit(code=1) from exc
    except ConfigurationError as exc:
        display.show_error("Configuration Error", str(exc))
        raise typer.Exit(code=1) from exc
    except SearchMuseError as exc:
        display.show_error("Search Error", str(exc))
        raise typer.Exit(code=1) from exc
    except KeyboardInterrupt:
        display.stop_progress()
        display.show_info("\nSearch interrupted.")
        raise typer.Exit(code=130) from None
    finally:
        display.stop_progress()


async def _async_search(
    container: Container,
    query: str,
) -> SearchResult:
    """Run the search and ensure cleanup."""
    try:
        return await container.orchestrator.run(query)
    finally:
        await container.close()


@config_app.command("show")
def config_show(
    config_path: Path | None = typer.Option(
        None, "--config", "-c", help="Path to custom config YAML",
    ),
) -> None:
    """Show the current resolved configuration."""
    display = Display()
    try:
        import dataclasses

        from searchmuse.infrastructure.config import load_config

        config = load_config(config_path)

        lines: list[str] = []
        for section_name in [
            "llm", "search", "scraping", "extraction", "storage", "output", "logging",
        ]:
            section = getattr(config, section_name)
            lines.append(f"[bold cyan]{section_name}[/]:")
            for field in dataclasses.fields(section):
                value = getattr(section, field.name)
                # Mask API keys in display
                if field.name == "api_key" and value is not None:
                    value = _mask_key(value)
                lines.append(f"  {field.name}: {value}")
            lines.append("")

        display.show_config("\n".join(lines))

    except ConfigurationError as exc:
        display.show_error("Configuration Error", str(exc))
        raise typer.Exit(code=1) from exc


@config_app.command("check")
def config_check(
    config_path: Path | None = typer.Option(
        None, "--config", "-c", help="Path to custom config YAML",
    ),
) -> None:
    """Check connectivity to required services."""
    display = Display()
    try:
        from searchmuse.infrastructure.config import load_config

        config = load_config(config_path)
        provider = config.llm.provider

        display.show_info(f"Checking services (provider: {provider})...\n")

        if provider == "ollama":
            ollama_ok = _check_ollama(config.llm.base_url, config.llm.model)
            display.show_check_result(
                ok=ollama_ok,
                service="Ollama",
                detail=(
                    f"Connected to {config.llm.base_url} (model: {config.llm.model})"
                    if ollama_ok
                    else f"Cannot reach {config.llm.base_url}"
                ),
            )
            if not ollama_ok:
                raise typer.Exit(code=1)
        else:
            api_key_ok = _check_api_key(provider, config.llm.api_key)
            display.show_check_result(
                ok=api_key_ok,
                service=f"{provider.capitalize()} API Key",
                detail="API key resolved" if api_key_ok else "No API key found",
            )
            if not api_key_ok:
                raise typer.Exit(code=1)

        display.show_check_result(
            ok=True,
            service="DuckDuckGo",
            detail="Search backend available (no auth required)",
        )

        db_path = Path(config.storage.db_path).expanduser()
        db_dir_ok = db_path.parent.exists() or not db_path.parent.is_absolute()
        display.show_check_result(
            ok=db_dir_ok,
            service="SQLite",
            detail=f"Database path: {db_path}",
        )

    except ConfigurationError as exc:
        display.show_error("Configuration Error", str(exc))
        raise typer.Exit(code=1) from exc


@config_app.command("set-key")
def config_set_key(
    provider: str = typer.Argument(..., help="LLM provider name (claude, openai, gemini)"),
    api_key: str = typer.Argument(..., help="The API key to store"),
) -> None:
    """Store an API key in the system keyring."""
    display = Display()

    from searchmuse.infrastructure import keyring_store

    if not keyring_store.is_available():
        display.show_error(
            "Keyring Unavailable",
            "The 'keyring' package is not installed. "
            "Install it with: pip install 'searchmuse[keyring]'",
        )
        raise typer.Exit(code=1)

    ok = keyring_store.store_api_key(provider, api_key)
    if ok:
        display.show_info(f"API key for {provider!r} stored in system keyring.")
    else:
        display.show_error("Keyring Error", f"Failed to store API key for {provider!r}.")
        raise typer.Exit(code=1)


@config_app.command("get-key")
def config_get_key(
    provider: str = typer.Argument(..., help="LLM provider name (claude, openai, gemini)"),
) -> None:
    """Show the resolved API key (masked) for a provider."""
    display = Display()

    from searchmuse.infrastructure.api_key_resolver import resolve_api_key

    key = resolve_api_key(provider)
    if key:
        display.show_info(f"API key for {provider!r}: {_mask_key(key)}")
    else:
        display.show_info(f"No API key found for {provider!r}.")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _mask_key(key: str) -> str:
    """Return a masked version of an API key, showing only the last 4 chars."""
    if len(key) <= 8:
        return "****"
    return f"{'*' * (len(key) - 4)}{key[-4:]}"


def _check_ollama(base_url: str, model: str) -> bool:
    """Check if Ollama is reachable and the model is available."""
    try:
        import httpx

        response = httpx.get(f"{base_url}/api/tags", timeout=5.0)
        if response.status_code != 200:
            return False
        data = response.json()
        models = [m.get("name", "") for m in data.get("models", [])]
        return any(model in m for m in models)
    except Exception:
        return False


def _check_api_key(provider: str, config_api_key: str | None) -> bool:
    """Check if an API key is resolvable for the given provider."""
    from searchmuse.infrastructure.api_key_resolver import resolve_api_key

    return resolve_api_key(provider, config_api_key) is not None
