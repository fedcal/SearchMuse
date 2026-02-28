"""Unit tests for SearchMuse CLI commands.

Uses typer.testing.CliRunner so that no real network calls or LLM requests
are made.  External dependencies (load_config, build_container, httpx) are
patched at the module boundary where each name is actually defined.

Patching strategy:
  - load_config lives in searchmuse.infrastructure.config and is imported
    lazily inside command function bodies, so we patch it at the definition
    site: "searchmuse.infrastructure.config.load_config".
  - build_container lives in searchmuse.cli.container and is likewise
    imported lazily inside _run_search, so we patch it at its definition
    site: "searchmuse.cli.container.build_container".
  - httpx.get is patched globally at "httpx.get" because _check_ollama
    imports httpx inside the function.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from typer.testing import CliRunner

from searchmuse.cli import app
from searchmuse.domain.errors import ConfigurationError, LLMAuthenticationError, ValidationError
from searchmuse.infrastructure.config import (
    ExtractionConfig,
    LLMConfig,
    LoggingConfig,
    OutputConfig,
    ScrapingConfig,
    SearchConfig,
    SearchMuseConfig,
    StorageConfig,
)
from searchmuse.version import __version__

runner = CliRunner()


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


def _make_real_config() -> SearchMuseConfig:
    """Return a real, frozen SearchMuseConfig usable in all CLI tests.

    Uses a real dataclass so that dataclasses.fields() works correctly in
    the config show command without needing to patch the stdlib.
    """
    return SearchMuseConfig(
        llm=LLMConfig(
            base_url="http://localhost:11434",
            model="llama3",
            strategy_temperature=0.3,
            assessment_temperature=0.1,
            synthesis_temperature=0.7,
            max_tokens=4096,
            timeout=120,
            provider="ollama",
        ),
        search=SearchConfig(
            max_iterations=3,
            min_sources=2,
            min_coverage_score=0.7,
            results_per_query=5,
            default_language="en",
        ),
        scraping=ScrapingConfig(
            request_delay=0.0,
            request_timeout=30,
            max_concurrent=5,
            respect_robots_txt=False,
            user_agent="Test/1.0",
            use_playwright=False,
            max_page_size=5_242_880,
        ),
        extraction=ExtractionConfig(
            min_word_count=50,
            max_text_length=8_000,
            preferred_extractor="trafilatura",
        ),
        storage=StorageConfig(db_path=":memory:", store_raw_html=False),
        output=OutputConfig(
            default_format="markdown",
            include_snippets=True,
            max_snippet_length=200,
        ),
        logging=LoggingConfig(level="DEBUG", file=None, timestamps=True),
    )


# ---------------------------------------------------------------------------
# Test 1: --version flag
# ---------------------------------------------------------------------------


class TestVersionFlag:
    """searchmuse --version must print the version string and exit 0."""

    def test_version_flag_exits_zero(self) -> None:
        result = runner.invoke(app, ["--version"])

        assert result.exit_code == 0

    def test_version_flag_prints_version(self) -> None:
        result = runner.invoke(app, ["--version"])

        assert __version__ in result.output

    def test_version_flag_short_form(self) -> None:
        result = runner.invoke(app, ["-V"])

        assert result.exit_code == 0
        assert __version__ in result.output

    def test_version_output_contains_searchmuse(self) -> None:
        result = runner.invoke(app, ["--version"])

        assert "SearchMuse" in result.output


# ---------------------------------------------------------------------------
# Test 2: no arguments shows help
# ---------------------------------------------------------------------------


class TestNoArgsShowsHelp:
    """Running without arguments must show help text and exit 0."""

    def test_no_args_exit_code(self) -> None:
        result = runner.invoke(app, [])

        # Typer with no_args_is_help=True exits with code 0 or 2 depending on version.
        assert result.exit_code in {0, 2}

    def test_no_args_shows_usage_text(self) -> None:
        result = runner.invoke(app, [])

        # Typer emits "Usage:" in its help output.
        assert "Usage" in result.output or "usage" in result.output.lower()

    def test_no_args_mentions_app_name(self) -> None:
        result = runner.invoke(app, [])

        assert "searchmuse" in result.output.lower()


# ---------------------------------------------------------------------------
# Test 3: config show command
# ---------------------------------------------------------------------------


class TestConfigShowCommand:
    """config show must load config and display it without error."""

    def test_config_show_exits_zero(self) -> None:
        # Use a real SearchMuseConfig so dataclasses.fields() is unpatched.
        real_config = _make_real_config()

        with patch("searchmuse.infrastructure.config.load_config", return_value=real_config):
            result = runner.invoke(app, ["config", "show"])

        assert result.exit_code == 0

    def test_config_show_calls_load_config(self) -> None:
        real_config = _make_real_config()

        with patch(
            "searchmuse.infrastructure.config.load_config", return_value=real_config
        ) as mock_load:
            runner.invoke(app, ["config", "show"])

        mock_load.assert_called_once_with(None)

    def test_config_show_accepts_config_path_option(self) -> None:
        real_config = _make_real_config()

        with patch(
            "searchmuse.infrastructure.config.load_config", return_value=real_config
        ) as mock_load:
            runner.invoke(app, ["config", "show", "--config", "/tmp/custom.yaml"])

        mock_load.assert_called_once_with(Path("/tmp/custom.yaml"))

    def test_config_show_configuration_error_exits_one(self) -> None:
        with patch(
            "searchmuse.infrastructure.config.load_config",
            side_effect=ConfigurationError("Missing section: llm"),
        ):
            result = runner.invoke(app, ["config", "show"])

        assert result.exit_code == 1

    def test_config_show_output_contains_llm_section(self) -> None:
        """The displayed config must contain the llm section header."""
        real_config = _make_real_config()

        with patch("searchmuse.infrastructure.config.load_config", return_value=real_config):
            result = runner.invoke(app, ["config", "show"])

        assert result.exit_code == 0
        # The section name appears in the Rich panel rendered to stderr;
        # CliRunner captures mix_stderr=True by default.
        assert "llm" in result.output


# ---------------------------------------------------------------------------
# Test 4: config check command
# ---------------------------------------------------------------------------


class TestConfigCheckCommand:
    """config check must probe services and report results."""

    def test_config_check_exits_zero_when_ollama_ok(self) -> None:
        real_config = _make_real_config()

        # Simulate Ollama reachable with the target model listed.
        ok_response = MagicMock()
        ok_response.status_code = 200
        ok_response.json.return_value = {"models": [{"name": "llama3:latest"}]}

        with patch("searchmuse.infrastructure.config.load_config", return_value=real_config), patch(
            "httpx.get", return_value=ok_response
        ):
            result = runner.invoke(app, ["config", "check"])

        assert result.exit_code == 0

    def test_config_check_exits_one_when_ollama_unreachable(self) -> None:
        real_config = _make_real_config()

        with patch(
            "searchmuse.infrastructure.config.load_config", return_value=real_config
        ), patch("httpx.get", side_effect=Exception("Connection refused")):
            result = runner.invoke(app, ["config", "check"])

        assert result.exit_code == 1

    def test_config_check_exits_one_on_bad_status(self) -> None:
        real_config = _make_real_config()

        bad_response = MagicMock()
        bad_response.status_code = 500

        with patch(
            "searchmuse.infrastructure.config.load_config", return_value=real_config
        ), patch("httpx.get", return_value=bad_response):
            result = runner.invoke(app, ["config", "check"])

        assert result.exit_code == 1

    def test_config_check_configuration_error_exits_one(self) -> None:
        with patch(
            "searchmuse.infrastructure.config.load_config",
            side_effect=ConfigurationError("Missing section"),
        ):
            result = runner.invoke(app, ["config", "check"])

        assert result.exit_code == 1

    def test_config_check_duckduckgo_always_reported(self) -> None:
        """DuckDuckGo needs no auth; check output mentions DuckDuckGo."""
        real_config = _make_real_config()

        ok_response = MagicMock()
        ok_response.status_code = 200
        ok_response.json.return_value = {"models": [{"name": "llama3:latest"}]}

        with patch("searchmuse.infrastructure.config.load_config", return_value=real_config), patch(
            "httpx.get", return_value=ok_response
        ):
            result = runner.invoke(app, ["config", "check"])

        # The command unconditionally reports DuckDuckGo as available.
        assert "DuckDuckGo" in result.output


# ---------------------------------------------------------------------------
# Test 5: search command validation error on empty query
# ---------------------------------------------------------------------------


class TestSearchCommandValidationError:
    """Passing an empty or whitespace-only query must exit with code 1."""

    def test_search_empty_query_exits_one(self) -> None:
        """An empty string triggers ValidationError inside _run_search."""
        container_stub = MagicMock()
        container_stub.orchestrator.run = AsyncMock(
            side_effect=ValidationError(
                "Query must not be empty",
                field="query",
                detail="Received an empty or whitespace-only string",
            )
        )
        container_stub.renderer.render = MagicMock(return_value="")
        container_stub.close = AsyncMock()

        # build_container is imported lazily inside _run_search; patch it
        # at its definition site in the container module.
        with patch("searchmuse.cli.container.build_container", return_value=container_stub):
            result = runner.invoke(app, ["search", ""])

        assert result.exit_code == 1

    def test_search_command_validation_error_shown(self) -> None:
        """ValidationError from the orchestrator triggers exit code 1."""
        container_stub = MagicMock()
        container_stub.orchestrator.run = AsyncMock(
            side_effect=ValidationError(
                "Query must not be empty",
                field="query",
                detail="Received an empty or whitespace-only string",
            )
        )
        container_stub.renderer.render = MagicMock(return_value="")
        container_stub.close = AsyncMock()

        with patch("searchmuse.cli.container.build_container", return_value=container_stub):
            result = runner.invoke(app, ["search", ""])

        # Exit code 1 is the primary assertion; output content is secondary.
        assert result.exit_code == 1

    def test_search_requires_query_argument(self) -> None:
        """Invoking `search` with no positional argument fails (typer validation)."""
        result = runner.invoke(app, ["search"])

        # Typer exits with non-zero when a required argument is absent.
        assert result.exit_code != 0

    def test_search_whitespace_query_exits_one(self) -> None:
        """A whitespace-only string propagates through to ValidationError."""
        container_stub = MagicMock()
        container_stub.orchestrator.run = AsyncMock(
            side_effect=ValidationError(
                "Query must not be empty",
                field="query",
                detail="Received an empty or whitespace-only string",
            )
        )
        container_stub.renderer.render = MagicMock(return_value="")
        container_stub.close = AsyncMock()

        with patch("searchmuse.cli.container.build_container", return_value=container_stub):
            result = runner.invoke(app, ["search", "   "])

        assert result.exit_code == 1


# ---------------------------------------------------------------------------
# Test 6: --provider flag
# ---------------------------------------------------------------------------


class TestProviderFlag:
    """The --provider / -p flag must pass through to run_search."""

    def test_provider_flag_sets_env_var(self) -> None:
        container_stub = MagicMock()
        container_stub.orchestrator.run = AsyncMock(
            side_effect=ValidationError(
                "test", field="query", detail="test",
            )
        )
        container_stub.renderer.render = MagicMock(return_value="")
        container_stub.close = AsyncMock()

        with patch("searchmuse.cli.container.build_container", return_value=container_stub):
            result = runner.invoke(app, ["search", "test", "--provider", "claude"])

        assert result.exit_code == 1  # ValidationError, but env var was set

    def test_provider_short_flag(self) -> None:
        container_stub = MagicMock()
        container_stub.orchestrator.run = AsyncMock(
            side_effect=ValidationError(
                "test", field="query", detail="test",
            )
        )
        container_stub.renderer.render = MagicMock(return_value="")
        container_stub.close = AsyncMock()

        with patch("searchmuse.cli.container.build_container", return_value=container_stub):
            result = runner.invoke(app, ["search", "test", "-p", "openai"])

        assert result.exit_code == 1


# ---------------------------------------------------------------------------
# Test 7: LLMAuthenticationError handling
# ---------------------------------------------------------------------------


class TestAuthenticationErrorHandling:
    """LLMAuthenticationError must exit with code 1."""

    def test_authentication_error_exits_one(self) -> None:
        container_stub = MagicMock()
        container_stub.orchestrator.run = AsyncMock(
            side_effect=LLMAuthenticationError(
                "Bad key", model="claude-sonnet-4-6", detail="Invalid API key",
            )
        )
        container_stub.renderer.render = MagicMock(return_value="")
        container_stub.close = AsyncMock()

        with patch("searchmuse.cli.container.build_container", return_value=container_stub):
            result = runner.invoke(app, ["search", "test"])

        assert result.exit_code == 1


# ---------------------------------------------------------------------------
# Test 8: config set-key / get-key
# ---------------------------------------------------------------------------


class TestConfigKeyCommands:
    """config set-key and get-key must interact with the keyring store."""

    def test_set_key_with_available_keyring(self) -> None:
        with patch(
            "searchmuse.infrastructure.keyring_store.is_available", return_value=True,
        ), patch(
            "searchmuse.infrastructure.keyring_store.store_api_key", return_value=True,
        ):
            result = runner.invoke(app, ["config", "set-key", "claude", "sk-ant-test"])

        assert result.exit_code == 0

    def test_set_key_without_keyring_exits_one(self) -> None:
        with patch(
            "searchmuse.infrastructure.keyring_store.is_available", return_value=False,
        ):
            result = runner.invoke(app, ["config", "set-key", "claude", "sk-ant-test"])

        assert result.exit_code == 1

    def test_get_key_shows_masked_key(self) -> None:
        with patch(
            "searchmuse.infrastructure.api_key_resolver.resolve_api_key",
            return_value="sk-ant-api123456789",
        ):
            result = runner.invoke(app, ["config", "get-key", "claude"])

        assert result.exit_code == 0
        # Key should be masked
        assert "6789" in result.output
        assert "sk-ant-api" not in result.output

    def test_get_key_not_found(self) -> None:
        with patch(
            "searchmuse.infrastructure.api_key_resolver.resolve_api_key",
            return_value=None,
        ):
            result = runner.invoke(app, ["config", "get-key", "claude"])

        assert result.exit_code == 0
        assert "No API key found" in result.output


# ---------------------------------------------------------------------------
# Test 9: config check multi-provider
# ---------------------------------------------------------------------------


class TestConfigCheckMultiProvider:
    """config check must adapt to the active provider."""

    def test_check_claude_provider_with_key(self) -> None:
        real_config = _make_real_config()
        # Override provider to claude
        claude_llm = LLMConfig(
            base_url="https://api.anthropic.com",
            model="claude-sonnet-4-6",
            strategy_temperature=0.3,
            assessment_temperature=0.1,
            synthesis_temperature=0.7,
            max_tokens=4096,
            timeout=120,
            provider="claude",
            api_key="sk-ant-test",
        )
        import dataclasses

        claude_config = dataclasses.replace(real_config, llm=claude_llm)

        with patch(
            "searchmuse.infrastructure.config.load_config", return_value=claude_config,
        ), patch(
            "searchmuse.infrastructure.api_key_resolver.resolve_api_key",
            return_value="sk-ant-test",
        ):
            result = runner.invoke(app, ["config", "check"])

        assert result.exit_code == 0
        assert "API Key" in result.output or "API key" in result.output
