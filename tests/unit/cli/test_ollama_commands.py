"""Tests for searchmuse.cli.ollama_commands."""

from unittest.mock import patch

from typer.testing import CliRunner

from searchmuse.cli import app
from searchmuse.infrastructure.ollama_client import OllamaModel

runner = CliRunner()

_MOD = "searchmuse.cli.ollama_commands"


@patch(f"{_MOD}._get_base_url", return_value="http://localhost:11434")
@patch("searchmuse.infrastructure.ollama_client.is_reachable", return_value=False)
def test_ollama_list_unreachable(mock_reachable, mock_url):
    result = runner.invoke(app, ["ollama", "list"])
    assert result.exit_code == 1
    assert "Cannot reach" in result.output


@patch(f"{_MOD}._get_base_url", return_value="http://localhost:11434")
@patch("searchmuse.infrastructure.ollama_client.list_models", return_value=())
@patch("searchmuse.infrastructure.ollama_client.is_reachable", return_value=True)
def test_ollama_list_empty(mock_reachable, mock_list, mock_url):
    result = runner.invoke(app, ["ollama", "list"])
    assert result.exit_code == 0
    assert "No models" in result.output


@patch(f"{_MOD}._get_base_url", return_value="http://localhost:11434")
@patch("searchmuse.infrastructure.ollama_client.list_models")
@patch("searchmuse.infrastructure.ollama_client.is_reachable", return_value=True)
def test_ollama_list_with_models(mock_reachable, mock_list, mock_url):
    mock_list.return_value = (
        OllamaModel(name="mistral:latest", size_bytes=4_000_000_000, modified_at="2024-01-01T00:00:00Z"),
    )
    result = runner.invoke(app, ["ollama", "list"])
    assert result.exit_code == 0
    assert "mistral" in result.output


@patch(f"{_MOD}._get_base_url", return_value="http://localhost:11434")
@patch("searchmuse.infrastructure.ollama_client.is_reachable", return_value=False)
def test_ollama_pull_unreachable(mock_reachable, mock_url):
    result = runner.invoke(app, ["ollama", "pull", "mistral"])
    assert result.exit_code == 1


@patch(f"{_MOD}._get_base_url", return_value="http://localhost:11434")
@patch("searchmuse.infrastructure.ollama_client.model_exists", return_value=True)
@patch("searchmuse.infrastructure.ollama_client.is_reachable", return_value=True)
def test_ollama_select_exists(mock_reachable, mock_exists, mock_url):
    result = runner.invoke(app, ["ollama", "select", "mistral"])
    assert result.exit_code == 0
    assert "available" in result.output


@patch(f"{_MOD}._get_base_url", return_value="http://localhost:11434")
@patch("searchmuse.infrastructure.ollama_client.model_exists", return_value=False)
@patch("searchmuse.infrastructure.ollama_client.is_reachable", return_value=True)
def test_ollama_select_not_installed(mock_reachable, mock_exists, mock_url):
    result = runner.invoke(app, ["ollama", "select", "notexist"])
    assert result.exit_code == 1
    assert "not installed" in result.output
