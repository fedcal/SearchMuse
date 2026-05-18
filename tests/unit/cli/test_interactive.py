"""Unit tests for SearchMuse interactive REPL session.

Tests the InteractiveSession class with mocked input/output
and container dependencies.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from searchmuse.cli.interactive import (
    InteractiveSession,
    _parse_interactive_input,
)

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _make_session(**kwargs):
    """Create an InteractiveSession with default mocks."""
    return InteractiveSession(**kwargs)


def _patch_load_config(config=None):
    """Patch load_config to return None or a given config."""
    return patch(
        "searchmuse.infrastructure.config.load_config",
        return_value=config,
    )


# ---------------------------------------------------------------------------
# Test: _parse_interactive_input
# ---------------------------------------------------------------------------


class TestParseInteractiveInput:
    """_parse_interactive_input extracts flags from raw input."""

    def test_plain_query(self) -> None:
        query, provider, max_iter = _parse_interactive_input("quantum computing trends")

        assert query == "quantum computing trends"
        assert provider is None
        assert max_iter is None

    def test_provider_flag(self) -> None:
        query, provider, max_iter = _parse_interactive_input("AI safety -p claude")

        assert query == "AI safety"
        assert provider == "claude"
        assert max_iter is None

    def test_iterations_flag(self) -> None:
        query, provider, max_iter = _parse_interactive_input("deep learning -i 3")

        assert query == "deep learning"
        assert provider is None
        assert max_iter == 3

    def test_both_flags(self) -> None:
        query, provider, max_iter = _parse_interactive_input(
            "machine learning -p openai -i 2"
        )

        assert query == "machine learning"
        assert provider == "openai"
        assert max_iter == 2

    def test_flags_at_start(self) -> None:
        query, provider, _max_iter = _parse_interactive_input("-p gemini AI news")

        assert query == "AI news"
        assert provider == "gemini"

    def test_invalid_iterations_ignored(self) -> None:
        query, _provider, max_iter = _parse_interactive_input("test query -i abc")

        assert query == "test query"
        assert max_iter is None

    def test_trailing_flag_without_value(self) -> None:
        query, provider, _max_iter = _parse_interactive_input("test query -p")

        assert query == "test query -p"
        assert provider is None


# ---------------------------------------------------------------------------
# Test: InteractiveSession exit commands
# ---------------------------------------------------------------------------


class TestInteractiveExitCommands:
    """The REPL exits cleanly on exit/quit/q and Ctrl+D."""

    def test_exit_command(self) -> None:
        with (
            _patch_load_config(),
            patch.object(InteractiveSession, "_read_input", return_value="exit"),
            patch("searchmuse.cli.display.Display.show_banner"),
        ):
            session = _make_session()
            session.run()

    def test_quit_command(self) -> None:
        with (
            _patch_load_config(),
            patch.object(InteractiveSession, "_read_input", return_value="quit"),
            patch("searchmuse.cli.display.Display.show_banner"),
        ):
            session = _make_session()
            session.run()

    def test_q_command(self) -> None:
        with (
            _patch_load_config(),
            patch.object(InteractiveSession, "_read_input", return_value="q"),
            patch("searchmuse.cli.display.Display.show_banner"),
        ):
            session = _make_session()
            session.run()

    def test_eof_exits_cleanly(self) -> None:
        with (
            _patch_load_config(),
            patch.object(
                InteractiveSession, "_read_input", side_effect=EOFError
            ),
            patch("searchmuse.cli.display.Display.show_banner"),
        ):
            session = _make_session()
            session.run()

    def test_keyboard_interrupt_exits_cleanly(self) -> None:
        with (
            _patch_load_config(),
            patch.object(
                InteractiveSession, "_read_input", side_effect=KeyboardInterrupt
            ),
            patch("searchmuse.cli.display.Display.show_banner"),
        ):
            session = _make_session()
            session.run()


# ---------------------------------------------------------------------------
# Test: help command
# ---------------------------------------------------------------------------


class TestInteractiveHelpCommand:
    """The 'help' command displays usage text."""

    def test_help_then_exit(self) -> None:
        inputs = iter(["help", "exit"])

        with (
            _patch_load_config(),
            patch.object(
                InteractiveSession, "_read_input", side_effect=inputs
            ),
            patch("searchmuse.cli.display.Display.show_banner"),
        ):
            session = _make_session()
            session.run()

    def test_question_mark_is_help(self) -> None:
        inputs = iter(["?", "exit"])

        with (
            _patch_load_config(),
            patch.object(
                InteractiveSession, "_read_input", side_effect=inputs
            ),
            patch("searchmuse.cli.display.Display.show_banner"),
        ):
            session = _make_session()
            session.run()


# ---------------------------------------------------------------------------
# Test: empty input is ignored
# ---------------------------------------------------------------------------


class TestInteractiveEmptyInput:
    """Empty or whitespace-only input is silently ignored."""

    def test_empty_input_loops(self) -> None:
        inputs = iter(["", "   ", "exit"])

        with (
            _patch_load_config(),
            patch.object(
                InteractiveSession, "_read_input", side_effect=inputs
            ),
            patch("searchmuse.cli.display.Display.show_banner"),
        ):
            session = _make_session()
            session.run()


# ---------------------------------------------------------------------------
# Test: query execution
# ---------------------------------------------------------------------------


class TestInteractiveQueryExecution:
    """A typed query triggers container build and orchestrator run."""

    def test_query_triggers_search(self) -> None:
        inputs = iter(["quantum computing", "exit"])

        mock_result = MagicMock()
        mock_result.session_id = "abc"
        mock_result.synthesis = "Test answer"
        mock_result.citations = ()
        mock_result.total_sources_found = 0
        mock_result.iterations_performed = 1
        mock_result.duration_seconds = 1.5

        mock_container = MagicMock()
        mock_container.orchestrator.run = AsyncMock(return_value=mock_result)
        mock_container.renderer.render.return_value = "## Answer\nTest"
        mock_container.close = AsyncMock()

        with (
            _patch_load_config(),
            patch.object(
                InteractiveSession, "_read_input", side_effect=inputs
            ),
            patch("searchmuse.cli.display.Display.show_banner"),
            patch("searchmuse.cli.display.Display.start_progress"),
            patch("searchmuse.cli.display.Display.stop_progress"),
            patch("searchmuse.cli.display.Display.show_result"),
            patch(
                "searchmuse.cli.container.build_container",
                return_value=mock_container,
            ),
        ):
            session = _make_session()
            session.run()

        mock_container.orchestrator.run.assert_called_once_with(
            "quantum computing", chat_context=(),
        )

    def test_query_with_provider_flag(self) -> None:
        inputs = iter(["AI safety -p claude", "exit"])

        mock_result = MagicMock()
        mock_container = MagicMock()
        mock_container.orchestrator.run = AsyncMock(return_value=mock_result)
        mock_container.renderer.render.return_value = "answer"
        mock_container.close = AsyncMock()

        with (
            _patch_load_config(),
            patch.object(
                InteractiveSession, "_read_input", side_effect=inputs
            ),
            patch("searchmuse.cli.display.Display.show_banner"),
            patch("searchmuse.cli.display.Display.start_progress"),
            patch("searchmuse.cli.display.Display.stop_progress"),
            patch("searchmuse.cli.display.Display.show_result"),
            patch(
                "searchmuse.cli.container.build_container",
                return_value=mock_container,
            ),
            patch.dict("os.environ", {}, clear=False),
        ):
            session = _make_session()
            session.run()

        mock_container.orchestrator.run.assert_called_once_with(
            "AI safety", chat_context=(),
        )


# ---------------------------------------------------------------------------
# Test: error handling in queries
# ---------------------------------------------------------------------------


class TestInteractiveErrorHandling:
    """Errors during search do not crash the REPL."""

    def test_validation_error_shows_message(self) -> None:
        from searchmuse.domain.errors import ValidationError

        inputs = iter(["bad query", "exit"])

        with (
            _patch_load_config(),
            patch.object(
                InteractiveSession, "_read_input", side_effect=inputs
            ),
            patch("searchmuse.cli.display.Display.show_banner"),
            patch("searchmuse.cli.display.Display.start_progress"),
            patch("searchmuse.cli.display.Display.stop_progress"),
            patch("searchmuse.cli.display.Display.show_error") as mock_error,
            patch(
                "searchmuse.cli.container.build_container",
                side_effect=ValidationError(
                    "too short", field="query", detail="Query is too short"
                ),
            ),
        ):
            session = _make_session()
            session.run()

        mock_error.assert_called_once()
        assert "Validation Error" in mock_error.call_args[0][0]

    def test_keyboard_interrupt_during_search(self) -> None:
        inputs = iter(["long query", "exit"])

        with (
            _patch_load_config(),
            patch.object(
                InteractiveSession, "_read_input", side_effect=inputs
            ),
            patch("searchmuse.cli.display.Display.show_banner"),
            patch("searchmuse.cli.display.Display.start_progress"),
            patch("searchmuse.cli.display.Display.stop_progress"),
            patch(
                "searchmuse.cli.container.build_container",
                side_effect=KeyboardInterrupt,
            ),
        ):
            session = _make_session()
            session.run()


# ---------------------------------------------------------------------------
# Test: banner is shown on startup
# ---------------------------------------------------------------------------


class TestInteractiveBannerDisplay:
    """The welcome banner is displayed when the session starts."""

    def test_banner_shown(self) -> None:
        with (
            _patch_load_config(),
            patch.object(
                InteractiveSession, "_read_input", return_value="exit"
            ),
            patch("searchmuse.cli.display.Display.show_banner") as mock_banner,
        ):
            session = _make_session()
            session.run()

        mock_banner.assert_called_once()


# ---------------------------------------------------------------------------
# Test: _show_models
# ---------------------------------------------------------------------------


def _make_config_mock(base_url: str = "http://localhost:11434", model: str = "llama3"):
    cfg = MagicMock()
    cfg.llm.base_url = base_url
    cfg.llm.model = model
    return cfg


class TestShowModels:
    """_show_models renders installed Ollama models, with error fallbacks."""

    def test_unreachable_prints_error(self) -> None:
        session = _make_session()
        session._console = MagicMock()
        with patch(
            "searchmuse.infrastructure.ollama_client.is_reachable",
            return_value=False,
        ):
            session._show_models(_make_config_mock())
        session._console.print.assert_called_once()

    def test_list_models_exception_prints_error(self) -> None:
        session = _make_session()
        session._console = MagicMock()
        with (
            patch(
                "searchmuse.infrastructure.ollama_client.is_reachable",
                return_value=True,
            ),
            patch(
                "searchmuse.infrastructure.ollama_client.list_models",
                side_effect=RuntimeError("boom"),
            ),
        ):
            session._show_models(_make_config_mock())
        session._console.print.assert_called_once()

    def test_empty_models_prints_hint(self) -> None:
        session = _make_session()
        session._console = MagicMock()
        with (
            patch(
                "searchmuse.infrastructure.ollama_client.is_reachable",
                return_value=True,
            ),
            patch(
                "searchmuse.infrastructure.ollama_client.list_models",
                return_value=(),
            ),
        ):
            session._show_models(_make_config_mock())
        session._console.print.assert_called_once()

    def test_populated_models_prints_table(self) -> None:
        session = _make_session()
        session._console = MagicMock()
        model_a = MagicMock()
        model_a.name = "llama3:latest"
        model_a.size_bytes = 4_000_000_000
        model_b = MagicMock()
        model_b.name = "mistral"
        model_b.size_bytes = 0
        with (
            patch(
                "searchmuse.infrastructure.ollama_client.is_reachable",
                return_value=True,
            ),
            patch(
                "searchmuse.infrastructure.ollama_client.list_models",
                return_value=(model_a, model_b),
            ),
        ):
            session._show_models(_make_config_mock(model="llama3"))
        session._console.print.assert_called_once()

    def test_none_config_uses_default_url(self) -> None:
        session = _make_session()
        session._console = MagicMock()
        with patch(
            "searchmuse.infrastructure.ollama_client.is_reachable",
            return_value=False,
        ) as mock_reach:
            session._show_models(None)
        mock_reach.assert_called_once_with("http://localhost:11434")


# ---------------------------------------------------------------------------
# Test: _switch_language
# ---------------------------------------------------------------------------


class TestSwitchLanguage:
    """_switch_language sets the UI language if supported."""

    def test_unsupported_language_warns(self) -> None:
        session = _make_session()
        session._console = MagicMock()
        session._switch_language("xx")
        session._console.print.assert_called_once()

    def test_supported_language_sets_and_confirms(self) -> None:
        session = _make_session()
        session._console = MagicMock()
        with patch(
            "searchmuse.infrastructure.i18n.set_language"
        ) as mock_set:
            session._switch_language("it")
        mock_set.assert_called_once_with("it")
        session._console.print.assert_called_once()


# ---------------------------------------------------------------------------
# Test: _switch_model
# ---------------------------------------------------------------------------


class TestSwitchModel:
    """_switch_model sets SEARCHMUSE_LLM_MODEL after validating Ollama."""

    def test_unreachable_prints_error(self) -> None:
        session = _make_session()
        session._console = MagicMock()
        with patch(
            "searchmuse.infrastructure.ollama_client.is_reachable",
            return_value=False,
        ):
            session._switch_model("llama3", _make_config_mock())
        session._console.print.assert_called_once()

    def test_model_missing_warns(self) -> None:
        session = _make_session()
        session._console = MagicMock()
        with (
            patch(
                "searchmuse.infrastructure.ollama_client.is_reachable",
                return_value=True,
            ),
            patch(
                "searchmuse.infrastructure.ollama_client.model_exists",
                return_value=False,
            ),
        ):
            session._switch_model("mystery", _make_config_mock())
        session._console.print.assert_called_once()

    def test_model_present_sets_env(self) -> None:
        import os

        session = _make_session()
        session._console = MagicMock()
        try:
            with (
                patch(
                    "searchmuse.infrastructure.ollama_client.is_reachable",
                    return_value=True,
                ),
                patch(
                    "searchmuse.infrastructure.ollama_client.model_exists",
                    return_value=True,
                ),
            ):
                session._switch_model("llama3", _make_config_mock())
            assert os.environ["SEARCHMUSE_LLM_MODEL"] == "llama3"
        finally:
            os.environ.pop("SEARCHMUSE_LLM_MODEL", None)


# ---------------------------------------------------------------------------
# Test: error paths in _execute_query
# ---------------------------------------------------------------------------


class TestExecuteQueryErrorPaths:
    """_execute_query maps each exception type to the right Display call."""

    def _run_with_error(self, exc: Exception) -> MagicMock:
        from contextlib import ExitStack

        inputs = iter(["a query", "exit"])
        with ExitStack() as stack:
            stack.enter_context(_patch_load_config())
            stack.enter_context(
                patch.object(
                    InteractiveSession, "_read_input", side_effect=inputs
                )
            )
            stack.enter_context(
                patch("searchmuse.cli.display.Display.show_banner")
            )
            stack.enter_context(
                patch("searchmuse.cli.display.Display.start_progress")
            )
            stack.enter_context(
                patch("searchmuse.cli.display.Display.stop_progress")
            )
            mock_error = stack.enter_context(
                patch("searchmuse.cli.display.Display.show_error")
            )
            stack.enter_context(
                patch(
                    "searchmuse.cli.container.build_container",
                    side_effect=exc,
                )
            )
            session = _make_session()
            session.run()
        return mock_error

    def test_llm_auth_error(self) -> None:
        from searchmuse.domain.errors import LLMAuthenticationError

        mock = self._run_with_error(
            LLMAuthenticationError("auth", model="claude", detail="401")
        )
        mock.assert_called_once()

    def test_llm_connection_error(self) -> None:
        from searchmuse.domain.errors import LLMConnectionError

        mock = self._run_with_error(
            LLMConnectionError("conn", model="claude", detail="refused")
        )
        mock.assert_called_once()

    def test_configuration_error(self) -> None:
        from searchmuse.domain.errors import ConfigurationError

        mock = self._run_with_error(ConfigurationError("bad config"))
        mock.assert_called_once()

    def test_generic_searchmuse_error(self) -> None:
        from searchmuse.domain.errors import SearchMuseError

        mock = self._run_with_error(SearchMuseError("oops"))
        mock.assert_called_once()


# ---------------------------------------------------------------------------
# Test: iteration flag triggers env override
# ---------------------------------------------------------------------------


class TestIterationFlagEnvOverride:
    """The -i flag sets SEARCHMUSE_SEARCH_MAXITERATIONS for the duration of the query."""

    def test_iteration_flag_sets_env(self) -> None:
        import os

        inputs = iter(["topic -i 5", "exit"])

        mock_result = MagicMock()
        mock_container = MagicMock()
        mock_container.orchestrator.run = AsyncMock(return_value=mock_result)
        mock_container.renderer.render.return_value = "answer"
        mock_container.close = AsyncMock()

        observed: dict[str, str] = {}

        def _capture_run(*args, **kwargs):
            observed["max"] = os.environ.get("SEARCHMUSE_SEARCH_MAXITERATIONS", "")
            return mock_result

        mock_container.orchestrator.run = AsyncMock(side_effect=_capture_run)

        with (
            _patch_load_config(),
            patch.object(
                InteractiveSession, "_read_input", side_effect=inputs
            ),
            patch("searchmuse.cli.display.Display.show_banner"),
            patch("searchmuse.cli.display.Display.start_progress"),
            patch("searchmuse.cli.display.Display.stop_progress"),
            patch("searchmuse.cli.display.Display.show_result"),
            patch(
                "searchmuse.cli.container.build_container",
                return_value=mock_container,
            ),
        ):
            session = _make_session()
            session.run()

        assert observed["max"] == "5"
        assert "SEARCHMUSE_SEARCH_MAXITERATIONS" not in os.environ


# ---------------------------------------------------------------------------
# Test: dispatch from run() to model/lang/chat handlers
# ---------------------------------------------------------------------------


class TestRunDispatch:
    """run() dispatches to the correct handler based on the input token."""

    def test_models_command_calls_show_models(self) -> None:
        inputs = iter(["models", "exit"])
        with (
            _patch_load_config(),
            patch.object(
                InteractiveSession, "_read_input", side_effect=inputs
            ),
            patch("searchmuse.cli.display.Display.show_banner"),
            patch.object(InteractiveSession, "_show_models") as mock_show,
        ):
            session = _make_session()
            session.run()
        mock_show.assert_called_once()

    def test_use_with_model_calls_switch(self) -> None:
        inputs = iter(["use llama3", "exit"])
        with (
            _patch_load_config(),
            patch.object(
                InteractiveSession, "_read_input", side_effect=inputs
            ),
            patch("searchmuse.cli.display.Display.show_banner"),
            patch.object(InteractiveSession, "_switch_model") as mock_switch,
        ):
            session = _make_session()
            session.run()
        mock_switch.assert_called_once()
        assert mock_switch.call_args[0][0] == "llama3"

    def test_lang_with_code_calls_switch(self) -> None:
        inputs = iter(["lang it", "exit"])
        with (
            _patch_load_config(),
            patch.object(
                InteractiveSession, "_read_input", side_effect=inputs
            ),
            patch("searchmuse.cli.display.Display.show_banner"),
            patch.object(InteractiveSession, "_switch_language") as mock_lang,
        ):
            session = _make_session()
            session.run()
        mock_lang.assert_called_once_with("it")

    def test_chat_command_routes_to_handler(self) -> None:
        inputs = iter(["new", "exit"])
        with (
            _patch_load_config(),
            patch.object(
                InteractiveSession, "_read_input", side_effect=inputs
            ),
            patch("searchmuse.cli.display.Display.show_banner"),
            patch.object(
                InteractiveSession, "_handle_chat_command"
            ) as mock_handle,
        ):
            session = _make_session()
            session.run()
        mock_handle.assert_called_once()
