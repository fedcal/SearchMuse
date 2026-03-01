"""Tests for searchmuse.infrastructure.ollama_client."""

from unittest.mock import MagicMock, patch

import httpx

from searchmuse.infrastructure.ollama_client import (
    OllamaModel,
    is_reachable,
    list_models,
    model_exists,
    pull_model,
)


@patch("searchmuse.infrastructure.ollama_client.httpx.get")
def test_is_reachable_success(mock_get):
    mock_get.return_value = MagicMock(status_code=200)
    assert is_reachable("http://localhost:11434") is True


@patch("searchmuse.infrastructure.ollama_client.httpx.get")
def test_is_reachable_failure(mock_get):
    mock_get.side_effect = httpx.ConnectError("refused")
    assert is_reachable("http://localhost:11434") is False


@patch("searchmuse.infrastructure.ollama_client.httpx.get")
def test_list_models(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "models": [
            {"name": "mistral:latest", "size": 4_000_000_000, "modified_at": "2024-01-01T00:00:00Z"},
            {"name": "llama3:latest", "size": 8_000_000_000, "modified_at": "2024-06-01T00:00:00Z"},
        ]
    }
    mock_get.return_value = mock_response

    models = list_models("http://localhost:11434")
    assert len(models) == 2
    assert isinstance(models[0], OllamaModel)
    assert models[0].name == "mistral:latest"
    assert models[1].size_bytes == 8_000_000_000


@patch("searchmuse.infrastructure.ollama_client.list_models")
def test_model_exists_true(mock_list):
    mock_list.return_value = (
        OllamaModel(name="mistral:latest", size_bytes=0, modified_at=""),
    )
    assert model_exists("http://localhost:11434", "mistral") is True


@patch("searchmuse.infrastructure.ollama_client.list_models")
def test_model_exists_false(mock_list):
    mock_list.return_value = (
        OllamaModel(name="mistral:latest", size_bytes=0, modified_at=""),
    )
    assert model_exists("http://localhost:11434", "llama3") is False


@patch("searchmuse.infrastructure.ollama_client.list_models")
def test_model_exists_on_error(mock_list):
    mock_list.side_effect = httpx.ConnectError("refused")
    assert model_exists("http://localhost:11434", "mistral") is False


@patch("searchmuse.infrastructure.ollama_client._pull_stream")
def test_pull_model_calls_callback(mock_stream):
    mock_stream.return_value = iter([
        {"status": "pulling", "completed": 100, "total": 1000},
        {"status": "pulling", "completed": 1000, "total": 1000},
        {"status": "success"},
    ])
    calls = []
    pull_model("http://localhost:11434", "test-model", progress_callback=lambda c, t, s: calls.append((c, t, s)))
    assert len(calls) == 3
    assert calls[-1][2] == "success"
