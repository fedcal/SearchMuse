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

        mock_container.orchestrator.run.assert_called_once_with("quantum computing")

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

        mock_container.orchestrator.run.assert_called_once_with("AI safety")


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
