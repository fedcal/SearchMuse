# Coding Conventions

**Analysis Date:** 2026-05-18

## Naming Patterns

**Modules / files:**
- `snake_case.py` for every module. Examples: `search_orchestrator.py`, `httpx_scraper.py`, `keyring_store.py`, `api_key_resolver.py`.
- Provider-specific adapters live in a sub-package and use a `<provider>_adapter.py` suffix (e.g. `ollama_adapter.py`, `claude_adapter.py`, `openai_adapter.py`, `gemini_adapter.py` under `src/searchmuse/adapters/llm/`).
- Internal/shared helpers inside an adapter package use a leading underscore: `_base.py`, `_factory.py`, `_helpers.py`, `_defaults.py` (see `src/searchmuse/adapters/llm/`).
- Port protocols use the `_port.py` suffix and live under `src/searchmuse/ports/` (e.g. `llm_port.py`, `scraper_port.py`, `chat_repository_port.py`).

**Classes:**
- `PascalCase`. Examples: `SearchOrchestrator`, `HttpxScraperAdapter`, `OllamaLLMAdapter`, `SearchMuseConfig`.
- Adapter classes end with `Adapter`; port classes end with `Port`; error classes end with `Error`.
- Custom exception base is `SearchMuseError`; provider-specific errors are `LLM*Error`, `Scraping*Error`, etc. (see `src/searchmuse/domain/errors.py`).

**Functions / methods:**
- `snake_case`. Public methods declared first, then internal helpers prefixed with `_` (e.g. `HttpxScraperAdapter._get_client`, `_enforce_rate_limit`, `_check_robots_txt` in `src/searchmuse/adapters/scrapers/httpx_scraper.py`).
- Async methods declared with `async def` follow the same naming rules.

**Constants:**
- Module-level constants are `UPPER_SNAKE_CASE` with a leading underscore when private to the module. Examples in `src/searchmuse/adapters/scrapers/httpx_scraper.py`: `_SCRAPER_ID`, `_CONTENT_TYPE_MAP`, `_ROBOTS_TXT_TIMEOUT`, `_ROBOTS_TXT_PATH`. Also `_DEFAULT_CONFIG_PATH`, `_ENV_PREFIX` in `src/searchmuse/infrastructure/config.py`, and `_QUERY_MIN_LENGTH`, `_QUERY_MAX_LENGTH`, `_ALLOWED_URL_SCHEMES` in `src/searchmuse/domain/validators.py`.
- Enums use `StrEnum` with `UPPER_SNAKE_CASE` members and lowercase string values (see `src/searchmuse/domain/enums.py`: `SearchPhase.INITIALIZING = "initializing"`, `RelevanceScore.HIGH = "high"`).

## Code Style

**Formatter / linter:** `ruff` (configured under `[tool.ruff]` in `pyproject.toml`).
- `line-length = 100`
- `target-version = "py311"`
- `src = ["src", "tests"]`

**Active rule sets** (`[tool.ruff.lint] select`):
- `E`, `W` (pycodestyle), `F` (pyflakes), `I` (isort), `N` (pep8-naming), `UP` (pyupgrade), `B` (flake8-bugbear), `SIM` (flake8-simplify), `TCH` (flake8-type-checking), `RUF` (ruff-specific).

**Ignored rules:** `E501` (line length handled elsewhere), `B008` (allows the standard Typer `typer.Option(...)` default-argument pattern used in `src/searchmuse/cli/commands.py`).

## Import Organization

Isort is configured via `[tool.ruff.lint.isort]` with `known-first-party = ["searchmuse"]`, producing this canonical ordering across the codebase:

1. `from __future__ import annotations` (almost always the first non-docstring line — see `src/searchmuse/domain/models.py`, `src/searchmuse/adapters/scrapers/httpx_scraper.py`, `src/searchmuse/application/search_orchestrator.py`).
2. Standard library imports (e.g. `import asyncio`, `import logging`, `from datetime import UTC, datetime`).
3. Third-party imports (e.g. `import httpx`, `import yaml`, `import ollama`, `import typer`).
4. First-party imports rooted at `searchmuse.*`.
5. `TYPE_CHECKING`-guarded imports gathered at the bottom of the import block (enforced by ruff `TCH`). Pattern from `src/searchmuse/adapters/scrapers/httpx_scraper.py`:

```python
from __future__ import annotations

import asyncio
import logging
import urllib.robotparser
import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING
from urllib.parse import urlparse

import httpx

from searchmuse.domain.enums import ContentType
from searchmuse.domain.errors import RequestTimeoutError, RobotsTxtBlockedError, ScrapingError
from searchmuse.domain.models import ScrapedPage

if TYPE_CHECKING:
    from searchmuse.infrastructure.config import ScrapingConfig
```

No path aliases; the package is imported by its fully-qualified dotted name `searchmuse.<sub>.<module>`.

## Docstring Style

Google-style docstrings throughout the codebase.

- Every public module starts with a one-line summary followed by a longer description (see headers of `src/searchmuse/domain/models.py`, `src/searchmuse/infrastructure/config.py`, `src/searchmuse/adapters/scrapers/httpx_scraper.py`).
- Every public class and function has a docstring with `Args:`, `Returns:`, and `Raises:` sections where applicable. Example from `src/searchmuse/adapters/scrapers/httpx_scraper.py`:

```python
async def scrape(self, url: str) -> ScrapedPage:
    """Fetch a single URL and return the raw page.

    Applies rate limiting and robots.txt checks before issuing the
    HTTP request. The page_id is generated as a fresh UUID4.

    Args:
        url: A validated http(s) URL to fetch.

    Returns:
        A frozen ScrapedPage with the raw HTML body and metadata.

    Raises:
        RobotsTxtBlockedError: When robots.txt disallows the URL and
            ``respect_robots_txt`` is enabled in config.
        RequestTimeoutError: When the request exceeds
            ``request_timeout`` seconds.
        ScrapingError: For any other httpx transport error.
    """
```

- Frozen dataclass fields are documented as bullet entries under an `Attributes:` section (see every dataclass in `src/searchmuse/domain/models.py`).
- Private helpers (leading underscore) still get docstrings when their behaviour is non-trivial.

## Type Annotation Policy

`mypy --strict` is enforced via `[tool.mypy]` in `pyproject.toml`:

- `strict = true`
- `disallow_untyped_defs = true`
- `disallow_incomplete_defs = true`
- `check_untyped_defs = true`
- `no_implicit_optional = true`
- `warn_return_any = true`
- `warn_redundant_casts = true`
- `warn_unused_ignores = true`

Practical consequences observed in the source:

- Every function/method (including private `_helpers`) has full parameter and return annotations, e.g. `def _extract_domain(url: str) -> str:` and `async def scrape_many(self, urls: tuple[str, ...]) -> tuple[ScrapedPage, ...]:`.
- `None` is always explicit: `api_key: str | None = None` (`src/searchmuse/infrastructure/config.py`), `progress: ProgressCallback | None = None` (`src/searchmuse/application/search_orchestrator.py`).
- PEP 604 unions (`X | Y`) are preferred over `typing.Union` thanks to `from __future__ import annotations` + Python 3.11+.
- Heavy-import types are placed under `if TYPE_CHECKING:` to keep runtime imports cheap (see `src/searchmuse/application/search_orchestrator.py` lines 29–36).
- Tests are exempted: `[[tool.mypy.overrides]] module = "tests.*"` sets `disallow_untyped_defs = false`.
- Third-party modules without stubs are silenced individually: `anthropic.*`, `openai.*`, `google.genai.*`, `keyring.*` have `ignore_missing_imports = true`.

## Error Handling

**Custom exception hierarchy** rooted at `SearchMuseError` in `src/searchmuse/domain/errors.py`:

- `ConfigurationError`
- `LLMError` → `LLMAuthenticationError`, `LLMConnectionError`, `LLMResponseError`
- `ScrapingError` → `RobotsTxtBlockedError`, `RequestTimeoutError`
- `ContentExtractionError`
- `ValidationError`
- `StorageError`

Errors carry structured context as keyword-only attributes (e.g. `model`, `detail`, `url`, `field`) and override `__str__` to produce a uniform, parseable message:

```python
class ScrapingError(SearchMuseError):
    def __init__(self, message: str, *, url: str) -> None:
        super().__init__(message)
        self.url = url

    def __str__(self) -> str:
        return f"Scraping error for {self.url!r}: {self.args[0]}"
```

**Translation pattern (`adapter → domain error`)** — third-party exceptions are caught and re-raised as domain errors with `raise ... from exc` to preserve the chain. From `src/searchmuse/adapters/scrapers/httpx_scraper.py`:

```python
except httpx.TimeoutException as exc:
    raise RequestTimeoutError(
        f"Request timed out after {self._config.request_timeout}s",
        url=url,
    ) from exc
except httpx.HTTPError as exc:
    raise ScrapingError(
        f"HTTP error while fetching {url!r}: {exc}",
        url=url,
    ) from exc
```

**Validation at boundaries** — raw input is validated by `src/searchmuse/domain/validators.py` (`validate_query`, `validate_url`, `validate_iteration_count`) which raise `ValidationError` with `field` and `detail` kwargs.

**Bulk operations swallow individual failures, log, return successes** — `HttpxScraperAdapter.scrape_many` logs `ScrapingError` as `warning` and unexpected exceptions as `error` with `exc_info=True`, then returns only the successful pages.

**No `Result` type**: the codebase uses exceptions everywhere, not a `Result[T, E]` wrapper.

## Async / Await Usage

- Pytest is in `asyncio_mode = "auto"`, so async tests do not need `@pytest.mark.asyncio`.
- All I/O adapters expose `async def` methods: `LLMPort`, `ScraperPort`, `ContentExtractorPort`, `SearchPort`, `SourceRepositoryPort`, `ChatRepositoryPort`.
- `SearchOrchestrator.run` is `async`; the CLI bridges sync→async with `asyncio.run(_async_search(...))` in `src/searchmuse/cli/commands.py`.
- Concurrency is bounded explicitly with `asyncio.Semaphore(self._config.max_concurrent)` in `HttpxScraperAdapter.scrape_many`, and per-domain rate limiting uses `asyncio.get_running_loop().time()` plus `asyncio.sleep(...)`.
- Async clients are created **lazily** inside the adapter (`_get_client`) so construction stays cheap and synchronous; `close()` is **idempotent** (`self._client = None` after `aclose()`).
- Async tests use `unittest.mock.AsyncMock` for port doubles (see `tests/unit/application/test_search_orchestrator.py`).

## Logging Patterns

- Every module that logs declares a module-level logger named after the module: `logger = logging.getLogger(__name__)` (or with explicit type `logger: logging.Logger = logging.getLogger(__name__)` in newer adapters such as `httpx_scraper.py`, `ollama_adapter.py`, `claude_adapter.py`, `gemini_adapter.py`, `openai_adapter.py`, `keyring_store.py`, `_base.py`).
- Use lazy `%`-formatting, never f-strings, in log calls: `logger.warning("Scrape failed, skipping URL %r: %s", url, exc)`.
- Levels: `debug` for I/O bookkeeping and lifecycle, `info` for user-visible state transitions, `warning` for recoverable failures, `error` for unexpected failures (`exc_info=True` when re-raising or swallowing).
- Root logger configuration lives in `src/searchmuse/infrastructure/logging_setup.py` (`setup_logging(config: LoggingConfig)`), which clears existing handlers, attaches a stderr `StreamHandler`, and optionally a `FileHandler`. Two format constants drive the layout depending on `config.timestamps`.
- User-facing strings flow through `searchmuse.infrastructure.i18n.t(...)` (translation helper), separate from logging.

## Configuration Loading

Centralised in `src/searchmuse/infrastructure/config.py`:

- Frozen `@dataclasses.dataclass(frozen=True, slots=True)` per section: `LLMConfig`, `SearchConfig`, `ScrapingConfig`, `ExtractionConfig`, `StorageConfig`, `OutputConfig`, `LoggingConfig`, plus the aggregate `SearchMuseConfig`.
- Layered precedence (low → high): `config/default.yaml` → user YAML at `config_path` → environment variables prefixed with `SEARCHMUSE_` (e.g. `SEARCHMUSE_LLM_MODEL`, `SEARCHMUSE_SEARCH_MAX_ITERATIONS`).
- Failure mode: any parse/typing problem raises `ConfigurationError` from `searchmuse.domain.errors`.
- The CLI may forward command-line overrides into env vars before calling `load_config`, e.g. in `run_search` (`src/searchmuse/cli/commands.py`) `os.environ["SEARCHMUSE_LLM_PROVIDER"] = provider`.

## Function and Module Design

- **Functions are small and single-purpose.** `HttpxScraperAdapter` splits work into `_get_client`, `_enforce_rate_limit`, `_check_robots_txt`, `_get_robots_parser`, `_fetch`, plus module-level helpers `_extract_domain` and `_detect_content_type`.
- **Files are focused.** Domain models, enums, errors, and validators each live in their own module under `src/searchmuse/domain/`. Adapters are split per technology (`httpx_scraper.py`, `playwright_scraper.py`, `duckduckgo_search.py`).
- **Section banners** with `# ---...---` comments separate "Public protocol methods", "Internal helpers", "Module-level helpers" etc. (see `httpx_scraper.py`, `config.py`).
- **Constructor injection** — orchestrator and adapters never instantiate their dependencies; they accept them through keyword-only `__init__` parameters (`SearchOrchestrator.__init__` uses `*,` then `llm`, `search`, `scraper`, ...).

## Immutability

- All domain models in `src/searchmuse/domain/models.py` use `@dataclasses.dataclass(frozen=True, slots=True)`.
- Mutating methods return a **new** instance via `dataclasses.replace(self, ...)`. Example from `SearchState`:

```python
def with_new_iteration(self, iteration: SearchIteration) -> SearchState:
    return dataclasses.replace(
        self,
        iterations=(*self.iterations, iteration),
    )
```

- Collections in domain objects are `tuple[...]`, never `list[...]`.
- Internal mutable caches in adapters (e.g. `HttpxScraperAdapter._robots_cache`, `_last_request_times`) are replaced wholesale with a new dict on each write rather than mutated in place: `self._robots_cache = {**self._robots_cache, domain: parser}`.

---

*Convention analysis: 2026-05-18*
