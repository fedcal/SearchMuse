"""Tests for searchmuse.infrastructure.config."""

import pytest

from searchmuse.domain.errors import ConfigurationError
from searchmuse.infrastructure.config import (
    SearchMuseConfig,
    _build_config,
    _coerce_env_value,
    _deep_merge,
    load_config,
)


def test_load_config_returns_frozen():
    config = load_config(None)
    assert isinstance(config, SearchMuseConfig)
    with pytest.raises(AttributeError):
        config.llm = None  # type: ignore[misc]


def test_load_config_defaults(monkeypatch):
    # Clean up any SEARCHMUSE_ env vars that might interfere
    import os
    for key in list(os.environ):
        if key.startswith("SEARCHMUSE_"):
            monkeypatch.delenv(key)
    config = load_config(None)
    assert config.llm.provider == "ollama"
    assert config.search.max_iterations == 5
    assert config.scraping.respect_robots_txt is True


def test_deep_merge_non_mutating():
    base = {"a": 1, "b": {"c": 2}}
    override = {"b": {"d": 3}}
    merged = _deep_merge(base, override)
    assert merged["b"]["c"] == 2
    assert merged["b"]["d"] == 3
    # Original unchanged
    assert "d" not in base["b"]


def test_deep_merge_override_scalar():
    base = {"a": 1}
    override = {"a": 99}
    merged = _deep_merge(base, override)
    assert merged["a"] == 99


def test_coerce_env_value_bool():
    assert _coerce_env_value("true", False) is True
    assert _coerce_env_value("false", True) is False
    assert _coerce_env_value("1", False) is True


def test_coerce_env_value_int():
    assert _coerce_env_value("42", 0) == 42


def test_coerce_env_value_float():
    assert _coerce_env_value("3.14", 0.0) == pytest.approx(3.14)


def test_coerce_env_value_string():
    assert _coerce_env_value("hello", "default") == "hello"


def test_coerce_env_value_none_reference():
    assert _coerce_env_value("raw", None) == "raw"


def test_build_config_missing_section():
    with pytest.raises(ConfigurationError, match="Missing required"):
        _build_config({"llm": {}})


def test_env_override(monkeypatch):
    monkeypatch.setenv("SEARCHMUSE_LLM_MODEL", "test-model")
    config = load_config(None)
    assert config.llm.model == "test-model"


def test_load_config_with_user_yaml(tmp_path):
    user_yaml = tmp_path / "custom.yaml"
    user_yaml.write_text("llm:\n  model: custom-model\n")
    config = load_config(user_yaml)
    assert config.llm.model == "custom-model"
