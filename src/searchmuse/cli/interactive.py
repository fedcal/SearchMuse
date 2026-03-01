"""Interactive REPL session for SearchMuse.

Provides a chat-like terminal interface where the user types research
queries and receives streamed progress updates followed by a markdown
result. The session starts with the welcome banner and loops until
the user types 'exit' or presses Ctrl+D.

Supports chat memory: conversations are persisted across sessions and
previous context is passed to the LLM for continuity.
"""

from __future__ import annotations

import asyncio
import contextlib
from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from rich.console import Console

from searchmuse.cli.display import Display
from searchmuse.domain.errors import (
    ConfigurationError,
    LLMAuthenticationError,
    LLMConnectionError,
    SearchMuseError,
    ValidationError,
)
from searchmuse.domain.models import ChatMessage, ChatSession
from searchmuse.infrastructure.i18n import t

if TYPE_CHECKING:
    from pathlib import Path

    from searchmuse.cli.container import Container
    from searchmuse.domain.models import SearchResult
    from searchmuse.infrastructure.config import SearchMuseConfig

_EXIT_COMMANDS: frozenset[str] = frozenset({"exit", "quit", "q"})
_HELP_COMMANDS: frozenset[str] = frozenset({"help", "?", "h"})
_MODELS_COMMANDS: frozenset[str] = frozenset({"models"})
_CHAT_COMMANDS: frozenset[str] = frozenset({
    "chats", "save", "load", "rename", "new", "context", "delete",
})

_PROMPT_MARKER = "[bold cyan]searchmuse>[/] "

def _build_help_text() -> str:
    """Build the help text using current language translations."""
    return (
        f"[bold cyan]{t('help_title')}[/]\n"
        f"\n"
        f"[bold yellow]{t('help_commands')}[/]\n"
        f"  [cyan]<query>[/]        {t('help_query')}\n"
        f"  [cyan]models[/]         {t('help_models')}\n"
        f"  [cyan]use <model>[/]    {t('help_use_model')}\n"
        f"  [cyan]lang <code>[/]    {t('help_lang')}\n"
        f"  [cyan]chats[/]          {t('help_chats')}\n"
        f"  [cyan]save [name][/]    {t('help_save')}\n"
        f"  [cyan]load <id|name>[/] {t('help_load')}\n"
        f"  [cyan]rename <name>[/]  {t('help_rename')}\n"
        f"  [cyan]new[/]            {t('help_new')}\n"
        f"  [cyan]context[/]        {t('help_context')}\n"
        f"  [cyan]delete <name>[/]  {t('help_delete_chat')}\n"
        f"  [cyan]help[/]           {t('help_help')}\n"
        f"  [cyan]exit[/]           {t('help_exit')}\n"
        f"\n"
        f"[bold yellow]{t('help_options')}[/]\n"
        f"  Use [bold]-p claude[/] {t('help_provider_flag')}\n"
        f"  Use [bold]-i 3[/] {t('help_iterations_flag')}\n"
        f"\n"
        f"[bold yellow]{t('help_examples')}[/]\n"
        f"  [dim]searchmuse>[/] What are the latest developments in quantum computing?\n"
        f"  [dim]searchmuse>[/] machine learning trends 2026 -p claude\n"
        f"  [dim]searchmuse>[/] AI safety breakthroughs -i 2\n"
        f"  [dim]searchmuse>[/] models\n"
        f"  [dim]searchmuse>[/] use llama3\n"
        f"  [dim]searchmuse>[/] save quantum-research\n"
        f"  [dim]searchmuse>[/] load quantum-research\n"
        f"\n"
        f"Press [bold]Ctrl+C[/] {t('help_ctrl_c')}\n"
        f"Press [bold]Ctrl+D[/] {t('help_ctrl_d')}\n"
    )


class InteractiveSession:
    """Chat-like REPL that runs searches and displays results interactively."""

    def __init__(
        self,
        *,
        config_path: Path | None = None,
        console: Console | None = None,
    ) -> None:
        self._config_path = config_path
        self._console = console or Console(stderr=True)
        self._output = Console()
        self._display = Display()
        self._current_chat: ChatSession | None = None
        self._chat_context: list[tuple[str, str]] = []

    def run(self) -> None:
        """Start the interactive session loop."""
        config = self._load_config()
        self._display.show_banner(config)

        self._console.print()
        self._console.print(f"[dim]{t('type_query_hint')}[/]")
        self._console.print()

        while True:
            try:
                raw_input = self._read_input()
            except (KeyboardInterrupt, EOFError):
                self._console.print(f"\n[dim]{t('goodbye')}[/]")
                break

            stripped = raw_input.strip()
            if not stripped:
                continue

            if stripped.lower() in _EXIT_COMMANDS:
                self._console.print(f"[dim]{t('goodbye')}[/]")
                break

            if stripped.lower() in _HELP_COMMANDS:
                self._console.print(_build_help_text())
                continue

            if stripped.lower() in _MODELS_COMMANDS:
                self._show_models(config)
                continue

            if stripped.lower().startswith("use "):
                model_name = stripped[4:].strip()
                if model_name:
                    self._switch_model(model_name, config)
                else:
                    self._console.print("[yellow]Usage: use <model>[/]")
                continue

            if stripped.lower().startswith("lang "):
                lang_code = stripped[5:].strip().lower()
                if lang_code:
                    self._switch_language(lang_code)
                else:
                    self._console.print("[yellow]Usage: lang <code> (en, it, fr, de, es)[/]")
                continue

            # Chat commands
            lower = stripped.lower()
            first_word = lower.split()[0] if lower else ""

            if first_word in _CHAT_COMMANDS:
                self._handle_chat_command(stripped, config)
                continue

            query, provider, max_iterations = _parse_interactive_input(stripped)
            self._execute_query(
                query=query,
                provider=provider,
                max_iterations=max_iterations,
                config=config,
            )

    def _read_input(self) -> str:
        """Read a single line of input from the user.

        Uses Rich markup for the prompt. Raises EOFError on Ctrl+D
        and KeyboardInterrupt on Ctrl+C at the prompt level.
        """
        from rich.text import Text

        self._console.print(Text.from_markup(_PROMPT_MARKER), end="")
        return input()

    def _show_models(self, config: SearchMuseConfig | None) -> None:
        """Display installed Ollama models in a table."""
        from rich.table import Table

        from searchmuse.infrastructure.ollama_client import is_reachable, list_models

        base_url = config.llm.base_url if config else "http://localhost:11434"

        if not is_reachable(base_url):
            self._console.print(
                f"[red]{t('ollama_unreachable', url=base_url)}[/]"
            )
            return

        try:
            models = list_models(base_url)
        except Exception as exc:
            self._console.print(f"[red]{t('error_fetching_models', error=exc)}[/]")
            return

        if not models:
            self._console.print(
                f"[yellow]{t('no_models_installed')}[/] "
                f"{t('pull_hint')}"
            )
            return

        current_model = config.llm.model if config else ""

        table = Table(border_style="cyan", show_header=True)
        table.add_column("Model", style="bold cyan")
        table.add_column("Size", justify="right")
        table.add_column("Active", justify="center")

        for m in models:
            size_mb = f"{m.size_bytes / (1024 * 1024):.0f} MB" if m.size_bytes > 0 else "—"
            active = "[green]*[/]" if current_model in m.name else ""
            table.add_row(m.name, size_mb, active)

        self._console.print(table)

    def _switch_language(self, lang_code: str) -> None:
        """Switch the UI language for the current session."""
        from searchmuse.infrastructure.i18n import SUPPORTED_LANGUAGES, set_language

        if lang_code not in SUPPORTED_LANGUAGES:
            supported = ", ".join(sorted(SUPPORTED_LANGUAGES))
            self._console.print(
                f"[yellow]{t('unsupported_lang', lang=lang_code, supported=supported)}[/]"
            )
            return

        set_language(lang_code)
        self._console.print(f"[green]{t('switched_lang', lang=lang_code)}[/]")

    def _switch_model(self, model_name: str, config: SearchMuseConfig | None) -> None:
        """Switch the active model for this session via environment variable."""
        import os

        from searchmuse.infrastructure.ollama_client import is_reachable, model_exists

        base_url = config.llm.base_url if config else "http://localhost:11434"

        if not is_reachable(base_url):
            self._console.print(f"[red]{t('ollama_unreachable', url=base_url)}[/]")
            return

        if not model_exists(base_url, model_name):
            self._console.print(
                f"[yellow]{t('model_not_installed', model=model_name)}[/]\n"
                f"{t('model_pull_first', model=model_name)}"
            )
            return

        os.environ["SEARCHMUSE_LLM_MODEL"] = model_name
        self._console.print(f"[green]{t('switched_model', model=model_name)}[/]")

    # ------------------------------------------------------------------
    # Chat commands
    # ------------------------------------------------------------------

    def _handle_chat_command(self, raw: str, config: SearchMuseConfig | None) -> None:
        """Dispatch a chat management command."""
        parts = raw.split(maxsplit=1)
        command = parts[0].lower()
        arg = parts[1].strip() if len(parts) > 1 else ""

        if command == "chats":
            asyncio.run(self._cmd_chats(config))
        elif command == "save":
            asyncio.run(self._cmd_save(arg, config))
        elif command == "load":
            asyncio.run(self._cmd_load(arg, config))
        elif command == "rename":
            if not arg:
                self._console.print("[yellow]Usage: rename <name>[/]")
            else:
                asyncio.run(self._cmd_rename(arg, config))
        elif command == "new":
            self._cmd_new()
        elif command == "context":
            self._cmd_context()
        elif command == "delete":
            if not arg:
                self._console.print("[yellow]Usage: delete <name|id>[/]")
            else:
                asyncio.run(self._cmd_delete(arg, config))

    async def _cmd_chats(self, config: SearchMuseConfig | None) -> None:
        """List all saved chat sessions."""
        from rich.table import Table

        repo = self._get_chat_repo(config)
        if repo is None:
            return
        try:
            sessions = await repo.list_sessions()
        finally:
            await repo.close()

        if not sessions:
            self._console.print(f"[dim]{t('chat_list_empty')}[/]")
            return

        table = Table(title=t("chat_list_title"), border_style="cyan")
        table.add_column(t("chat_col_id"), style="dim", max_width=10)
        table.add_column(t("chat_col_name"), style="bold cyan")
        table.add_column(t("chat_col_date"), justify="right")
        table.add_column(t("chat_col_messages"), justify="right")

        for s in sessions:
            table.add_row(
                s.session_id[:8],
                s.name,
                s.updated_at.strftime("%Y-%m-%d %H:%M"),
                str(len(s.messages)),
            )
        self._console.print(table)

    async def _cmd_save(self, name: str, config: SearchMuseConfig | None) -> None:
        """Save or rename the current chat session."""
        if self._current_chat is None:
            self._console.print(f"[yellow]{t('chat_no_context')}[/]")
            return

        effective_name = name if name else self._current_chat.name
        repo = self._get_chat_repo(config)
        if repo is None:
            return
        try:
            await repo.update_session_name(self._current_chat.session_id, effective_name)
        finally:
            await repo.close()

        now = datetime.now(UTC)
        self._current_chat = self._current_chat.with_name(effective_name, now)
        self._console.print(f"[green]{t('chat_saved', name=effective_name)}[/]")

    async def _cmd_load(self, identifier: str, config: SearchMuseConfig | None) -> None:
        """Load a previous chat session as current context."""
        repo = self._get_chat_repo(config)
        if repo is None:
            return
        try:
            session = await repo.load_session(identifier)
            if session is None:
                session = await repo.find_session_by_name(identifier)
        finally:
            await repo.close()

        if session is None:
            self._console.print(f"[yellow]{t('chat_not_found', name=identifier)}[/]")
            return

        self._current_chat = session
        self._chat_context = _extract_context(session)
        self._console.print(
            f"[green]{t('chat_loaded', name=session.name, count=len(session.messages))}[/]"
        )

    async def _cmd_rename(self, name: str, config: SearchMuseConfig | None) -> None:
        """Rename the current chat session."""
        if self._current_chat is None:
            self._console.print(f"[yellow]{t('chat_no_context')}[/]")
            return

        repo = self._get_chat_repo(config)
        if repo is None:
            return
        try:
            await repo.update_session_name(self._current_chat.session_id, name)
        finally:
            await repo.close()

        now = datetime.now(UTC)
        self._current_chat = self._current_chat.with_name(name, now)
        self._console.print(f"[green]{t('chat_renamed', name=name)}[/]")

    def _cmd_new(self) -> None:
        """Start a fresh chat session."""
        self._current_chat = None
        self._chat_context = []
        self._console.print(f"[green]{t('chat_new_started')}[/]")

    def _cmd_context(self) -> None:
        """Show a summary of the current chat context."""
        if not self._chat_context:
            self._console.print(f"[dim]{t('chat_no_context')}[/]")
            return

        self._console.print(
            f"[cyan]{t('chat_context_summary', count=len(self._chat_context))}[/]"
        )
        for idx, (q, s) in enumerate(self._chat_context, start=1):
            summary = s[:100].replace("\n", " ")
            self._console.print(f"  [dim]{idx}.[/] [bold]{q}[/]")
            self._console.print(f"     [dim]{summary}...[/]")

    async def _cmd_delete(self, identifier: str, config: SearchMuseConfig | None) -> None:
        """Delete a saved chat session."""
        repo = self._get_chat_repo(config)
        if repo is None:
            return
        try:
            session = await repo.load_session(identifier)
            if session is None:
                session = await repo.find_session_by_name(identifier)
            if session is None:
                self._console.print(f"[yellow]{t('chat_not_found', name=identifier)}[/]")
                return

            await repo.delete_session(session.session_id)
        finally:
            await repo.close()

        # Clear current chat if it was the deleted one
        if self._current_chat and self._current_chat.session_id == session.session_id:
            self._current_chat = None
            self._chat_context = []

        self._console.print(f"[green]{t('chat_deleted', name=session.name)}[/]")

    def _get_chat_repo(self, config: SearchMuseConfig | None) -> object | None:
        """Build a chat repository from config."""
        from searchmuse.adapters.repositories.sqlite_chat_repository import (
            SqliteChatRepositoryAdapter,
        )

        if config is None:
            self._console.print(f"[red]{t('config_error')}[/]")
            return None

        from pathlib import Path

        db_path = str(Path(config.storage.db_path).expanduser())
        return SqliteChatRepositoryAdapter(db_path=db_path)

    def _load_config(self) -> SearchMuseConfig | None:
        """Load configuration, returning None on failure."""
        from searchmuse.infrastructure.config import load_config

        config: SearchMuseConfig | None = None
        with contextlib.suppress(Exception):
            config = load_config(self._config_path)
        return config

    def _execute_query(
        self,
        *,
        query: str,
        provider: str | None,
        max_iterations: int | None,
        config: SearchMuseConfig | None,
    ) -> None:
        """Run a single search query with progress and display the result."""
        import os

        # Set env overrides for this query
        _env_overrides: dict[str, str] = {}
        if provider is not None:
            _env_overrides["SEARCHMUSE_LLM_PROVIDER"] = provider
            os.environ["SEARCHMUSE_LLM_PROVIDER"] = provider
        if max_iterations is not None:
            _env_overrides["SEARCHMUSE_SEARCH_MAXITERATIONS"] = str(max_iterations)
            os.environ["SEARCHMUSE_SEARCH_MAXITERATIONS"] = str(max_iterations)

        self._display.start_progress()

        try:
            from searchmuse.cli.container import build_container

            container = build_container(
                config_path=self._config_path,
                progress=self._display.make_progress_callback(),
            )

            chat_context = tuple(self._chat_context)
            result = asyncio.run(
                _async_search(container, query, chat_context)
            )
            rendered = container.renderer.render(result)
            self._display.show_result(result, rendered)

            # Save chat messages
            asyncio.run(
                self._save_chat_messages(query, result, config)
            )

        except ValidationError as exc:
            self._display.show_error(t("validation_error"), str(exc))
        except LLMAuthenticationError as exc:
            self._display.show_error(
                t("auth_error"),
                f"{exc}\n\n{t('check_api_key')}",
            )
        except LLMConnectionError as exc:
            self._display.show_error(
                t("connection_error"),
                f"{exc}\n\n{t('ensure_service')}",
            )
        except ConfigurationError as exc:
            self._display.show_error(t("config_error"), str(exc))
        except SearchMuseError as exc:
            self._display.show_error(t("search_error"), str(exc))
        except KeyboardInterrupt:
            self._display.stop_progress()
            self._console.print(f"\n[dim]{t('search_interrupted')}[/]")
        finally:
            self._display.stop_progress()
            # Restore env
            for key in _env_overrides:
                os.environ.pop(key, None)

    async def _save_chat_messages(
        self,
        query: str,
        result: SearchResult,
        config: SearchMuseConfig | None,
    ) -> None:
        """Save user/assistant messages and update chat context."""
        repo = self._get_chat_repo(config)
        if repo is None:
            return

        now = datetime.now(UTC)

        try:
            # Auto-create session on first query
            if self._current_chat is None:
                session_id = uuid4().hex[:12]
                auto_name = query[:50]
                session = ChatSession(
                    session_id=session_id,
                    name=auto_name,
                    messages=(),
                    created_at=now,
                    updated_at=now,
                )
                await repo.create_session(session)
                self._current_chat = session

            # Save user message
            user_msg = ChatMessage(
                message_id=uuid4().hex[:12],
                role="user",
                content=query,
                created_at=now,
            )
            await repo.save_message(self._current_chat.session_id, user_msg)

            # Save assistant message
            assistant_msg = ChatMessage(
                message_id=uuid4().hex[:12],
                role="assistant",
                content=result.synthesis,
                created_at=now,
                result_json="",
            )
            await repo.save_message(self._current_chat.session_id, assistant_msg)

            await repo.update_session_timestamp(self._current_chat.session_id)

            # Update in-memory state
            self._current_chat = self._current_chat.with_message(user_msg).with_message(
                assistant_msg
            )
            self._chat_context.append((query, result.synthesis))
        finally:
            await repo.close()


async def _async_search(
    container: Container,
    query: str,
    chat_context: tuple[tuple[str, str], ...] = (),
) -> SearchResult:
    """Run the search and ensure cleanup."""
    try:
        return await container.orchestrator.run(query, chat_context=chat_context)
    finally:
        await container.close()


def _extract_context(session: ChatSession) -> list[tuple[str, str]]:
    """Extract (query, synthesis) pairs from a loaded chat session."""
    context: list[tuple[str, str]] = []
    messages = session.messages
    i = 0
    while i < len(messages) - 1:
        if messages[i].role == "user" and messages[i + 1].role == "assistant":
            context.append((messages[i].content, messages[i + 1].content))
            i += 2
        else:
            i += 1
    return context


def _parse_interactive_input(
    raw: str,
) -> tuple[str, str | None, int | None]:
    """Parse interactive input, extracting inline flags.

    Supports:
      -p <provider>   Override LLM provider
      -i <number>     Override max iterations

    Returns:
        (query, provider, max_iterations) tuple.
    """
    parts = raw.split()
    query_parts: list[str] = []
    provider: str | None = None
    max_iterations: int | None = None

    i = 0
    while i < len(parts):
        if parts[i] == "-p" and i + 1 < len(parts):
            provider = parts[i + 1]
            i += 2
        elif parts[i] == "-i" and i + 1 < len(parts):
            with contextlib.suppress(ValueError):
                max_iterations = int(parts[i + 1])
            i += 2
        else:
            query_parts.append(parts[i])
            i += 1

    return " ".join(query_parts), provider, max_iterations
