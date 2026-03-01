"""Configuration loading for SearchMuse.

Loads values from (in ascending priority order):
  1. config/default.yaml bundled with the package
  2. A user-supplied YAML file at config_path
  3. Environment variables with the SEARCHMUSE_ prefix

Environment variable mapping examples:
  SEARCHMUSE_LLM_MODEL=llama3          → llm.model
  SEARCHMUSE_SEARCH_MAX_ITERATIONS=3   → search.max_iterations
  SEARCHMUSE_SCRAPING_REQUEST_DELAY=2  → scraping.request_delay
"""

from __future__ import annotations

import dataclasses
import os
from pathlib import Path
from typing import Any

import yaml

from searchmuse.domain.errors import ConfigurationError

_DEFAULT_CONFIG_PATH: Path = Path(__file__).parent.parent.parent.parent / "config" / "default.yaml"
_ENV_PREFIX: str = "SEARCHMUSE_"


# ---------------------------------------------------------------------------
# Frozen config dataclasses
# ---------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True, slots=True)
class LLMConfig:
    """Configuration for LLM backends (Ollama, Claude, OpenAI, Gemini)."""

    base_url: str
    model: str
    strategy_temperature: float
    assessment_temperature: float
    synthesis_temperature: float
    max_tokens: int
    timeout: int
    provider: str = "ollama"
    api_key: str | None = None


@dataclasses.dataclass(frozen=True, slots=True)
class SearchConfig:
    """Configuration controlling iterative search behaviour."""

    max_iterations: int
    min_sources: int
    min_coverage_score: float
    results_per_query: int
    default_language: str


@dataclasses.dataclass(frozen=True, slots=True)
class ScrapingConfig:
    """Configuration for the HTTP scraper adapter."""

    request_delay: float
    request_timeout: int
    max_concurrent: int
    respect_robots_txt: bool
    user_agent: str
    use_playwright: bool
    max_page_size: int


@dataclasses.dataclass(frozen=True, slots=True)
class ExtractionConfig:
    """Configuration for the content extraction adapter."""

    min_word_count: int
    max_text_length: int
    preferred_extractor: str


@dataclasses.dataclass(frozen=True, slots=True)
class StorageConfig:
    """Configuration for the source repository adapter."""

    db_path: str
    store_raw_html: bool


@dataclasses.dataclass(frozen=True, slots=True)
class OutputConfig:
    """Configuration for result rendering."""

    default_format: str
    include_snippets: bool
    max_snippet_length: int


@dataclasses.dataclass(frozen=True, slots=True)
class LoggingConfig:
    """Configuration for structured logging."""

    level: str
    file: str | None
    timestamps: bool
    ui_language: str = "en"


@dataclasses.dataclass(frozen=True, slots=True)
class SearchMuseConfig:
    """Top-level application configuration (immutable).

    Aggregates all sub-configurations into a single frozen object
    that is safe to pass across threads and async tasks.
    """

    llm: LLMConfig
    search: SearchConfig
    scraping: ScrapingConfig
    extraction: ExtractionConfig
    storage: StorageConfig
    output: OutputConfig
    logging: LoggingConfig


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML file, returning an empty dict when the file is absent."""
    if not path.exists():
        return {}
    try:
        with path.open(encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
            return data if isinstance(data, dict) else {}
    except yaml.YAMLError as exc:
        raise ConfigurationError(f"Failed to parse YAML at {path}: {exc}") from exc


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Return a new dict that is base merged with override (non-mutating)."""
    merged: dict[str, Any] = {**base}
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged = {**merged, key: _deep_merge(merged[key], value)}
        else:
            merged = {**merged, key: value}
    return merged


def _apply_env_overrides(raw: dict[str, Any]) -> dict[str, Any]:
    """Return a new config dict with environment variable overrides applied.

    Environment variable names follow the pattern:
        SEARCHMUSE_<SECTION>_<KEY>
    All keys are lowercased before matching. Values are coerced to the
    type of the existing config value (int, float, bool, or str).
    """
    result: dict[str, Any] = {**raw}

    for env_key, env_val in os.environ.items():
        if not env_key.startswith(_ENV_PREFIX):
            continue

        parts = env_key[len(_ENV_PREFIX):].lower().split("_", 1)
        if len(parts) != 2:
            continue

        section, key = parts
        if section not in result or not isinstance(result[section], dict):
            continue

        section_dict: dict[str, Any] = result[section]
        if key not in section_dict:
            continue

        coerced = _coerce_env_value(env_val, section_dict[key])
        result = {**result, section: {**section_dict, key: coerced}}

    return result


def _coerce_env_value(raw: str, reference: Any) -> Any:
    """Coerce a string env value to match the type of reference."""
    if reference is None:
        return raw
    if isinstance(reference, bool):
        return raw.lower() in {"true", "1", "yes"}
    if isinstance(reference, int):
        return int(raw)
    if isinstance(reference, float):
        return float(raw)
    return raw


def _build_config(raw: dict[str, Any]) -> SearchMuseConfig:
    """Construct a SearchMuseConfig from a raw merged dict.

    Raises:
        ConfigurationError: If required sections or keys are missing.
    """
    _require_section(raw, "llm")
    _require_section(raw, "search")
    _require_section(raw, "scraping")
    _require_section(raw, "extraction")
    _require_section(raw, "storage")
    _require_section(raw, "output")
    _require_section(raw, "logging")

    llm = LLMConfig(**raw["llm"])
    search = SearchConfig(**raw["search"])
    scraping = ScrapingConfig(**raw["scraping"])
    extraction = ExtractionConfig(**raw["extraction"])
    storage = StorageConfig(**raw["storage"])
    output = OutputConfig(**raw["output"])
    logging_cfg = LoggingConfig(**raw["logging"])

    return SearchMuseConfig(
        llm=llm,
        search=search,
        scraping=scraping,
        extraction=extraction,
        storage=storage,
        output=output,
        logging=logging_cfg,
    )


def _require_section(raw: dict[str, Any], section: str) -> None:
    """Raise ConfigurationError if a required section is missing."""
    if section not in raw or not isinstance(raw[section], dict):
        raise ConfigurationError(
            f"Missing required configuration section: '{section}'"
        )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def load_config(config_path: Path | None = None) -> SearchMuseConfig:
    """Load and return the application configuration.

    Merges configuration in ascending priority order:
      1. Defaults from config/default.yaml
      2. User overrides from config_path (if provided)
      3. Environment variable overrides (SEARCHMUSE_* prefix)

    Args:
        config_path: Optional path to a user-supplied YAML config file.
            When None, only defaults and env vars are used.

    Returns:
        A frozen SearchMuseConfig ready for use throughout the application.

    Raises:
        ConfigurationError: If any required section is missing or a YAML
            file cannot be parsed.
    """
    raw = _load_yaml(_DEFAULT_CONFIG_PATH)

    if config_path is not None:
        user_raw = _load_yaml(config_path)
        raw = _deep_merge(raw, user_raw)

    raw = _apply_env_overrides(raw)

    return _build_config(raw)
