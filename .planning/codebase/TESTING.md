# Testing Patterns

**Analysis Date:** 2026-05-18

## Test Framework

**Runner:** `pytest >= 8.0` (declared in `[project.optional-dependencies] dev` in `pyproject.toml`).

**Plugins:**
- `pytest-asyncio >= 0.24` — auto async test execution.
- `pytest-cov >= 5.0` — coverage with branch tracking.
- `respx >= 0.21` — `httpx`-native HTTP mocking (no real network calls).

**Assertion library:** stdlib `assert`.

**Mocking:** stdlib `unittest.mock` (`AsyncMock`, `MagicMock`, `patch`).

## Pytest Configuration

Configured in `pyproject.toml` under `[tool.pytest.ini_options]`:

```toml
testpaths = ["tests"]
pythonpath = ["src"]
asyncio_mode = "auto"
addopts = [
    "--strict-markers",
    "--tb=short",
    "-q",
]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks tests requiring external services",
]
```

- `pythonpath = ["src"]` lets tests import `searchmuse.*` without an editable install step.
- `asyncio_mode = "auto"` means every `async def test_*` is automatically awaited — **no `@pytest.mark.asyncio` decorator is needed** (see all `async def test_*` in `tests/unit/adapters/test_httpx_scraper.py`).
- `--strict-markers` forces every custom marker to be declared (i.e. `slow`, `integration`).
- `--tb=short -q` keeps CI output compact.

## Run Commands

```bash
# Run the whole suite
pytest

# Run a single file
pytest tests/unit/adapters/test_httpx_scraper.py

# Run a single test class or test function
pytest tests/unit/adapters/test_httpx_scraper.py::TestScrapeSuccess
pytest tests/unit/adapters/test_httpx_scraper.py::TestScrapeSuccess::test_returns_scraped_page_instance

# Filter by name substring
pytest -k "robots_txt"

# Skip slow tests (default CI behaviour for fast feedback)
pytest -m "not slow"

# Run only slow tests
pytest -m slow

# Run only integration tests (require external services)
pytest -m integration

# With coverage report and HTML output
pytest --cov=searchmuse --cov-branch --cov-report=term-missing --cov-report=html

# Fail fast on the first error
pytest -x
```

## Test File Organization

**Location:** all tests live under `tests/` mirroring the source package layout:

```
tests/
├── __init__.py
├── conftest.py
└── unit/
    ├── __init__.py
    ├── domain/
    │   ├── test_chat_models.py
    │   ├── test_enums.py
    │   ├── test_models.py
    │   └── test_validators.py
    ├── application/
    │   ├── test_orchestrator_context.py
    │   ├── test_progress.py
    │   └── test_search_orchestrator.py
    ├── infrastructure/
    │   ├── test_api_key_resolver.py
    │   ├── test_config.py
    │   ├── test_i18n.py
    │   ├── test_keyring_store.py
    │   ├── test_logging_setup.py
    │   └── test_ollama_client.py
    ├── adapters/
    │   ├── test_base_adapter.py
    │   ├── test_claude_adapter.py
    │   ├── test_duckduckgo_search.py
    │   ├── test_gemini_adapter.py
    │   ├── test_httpx_scraper.py
    │   ├── test_json_renderer.py
    │   ├── test_llm_defaults.py
    │   ├── test_llm_factory.py
    │   ├── test_llm_helpers.py
    │   ├── test_markdown_renderer.py
    │   ├── test_ollama_adapter.py
    │   ├── test_openai_adapter.py
    │   ├── test_plain_renderer.py
    │   ├── test_playwright_scraper.py
    │   ├── test_renderer_factory.py
    │   ├── test_sqlite_chat_repository.py
    │   ├── test_sqlite_repository.py
    │   └── test_trafilatura_extractor.py
    └── cli/
        ├── test_commands.py
        ├── test_container.py
        ├── test_display.py
        ├── test_interactive.py
        ├── test_interactive_chat.py
        └── test_ollama_commands.py
```

**Naming:** test files use the `test_<module>.py` pattern, mirroring the module under test (`httpx_scraper.py` → `test_httpx_scraper.py`).

## Existing Test Files (one-line purpose)

**`tests/conftest.py`** — Shared frozen-dataclass fixtures (`sample_query`, `sample_strategy`, `sample_source`, `sample_citation`, `sample_search_state`, `sample_iteration`, `sample_search_hit`, `sample_scraped_page`, `sample_extracted_content`, `sample_search_result`, `test_config`) built from `searchmuse.domain.models` and `searchmuse.infrastructure.config`.

**Domain layer (`tests/unit/domain/`):**
- `test_validators.py` — `validate_query`, `validate_url`, `validate_iteration_count` happy + error paths.
- `test_models.py` — Immutability and `with_*` replace semantics for `SearchState`, `Source`, `Citation`, etc.
- `test_chat_models.py` — `ChatSession.with_message`, `with_name` immutability semantics.
- `test_enums.py` — String values and membership of `SearchPhase`, `ContentType`, `RelevanceScore`, `SourceStatus`.

**Application layer (`tests/unit/application/`):**
- `test_search_orchestrator.py` — Drives `SearchOrchestrator.run` with `AsyncMock` ports across the full strategy → search → scrape → extract → assess → synthesize pipeline.
- `test_orchestrator_context.py` — Chat-context propagation into the LLM strategy call.
- `test_progress.py` — `ProgressEvent`, `NullProgress`, and callback contract.

**Infrastructure (`tests/unit/infrastructure/`):**
- `test_config.py` — YAML loading precedence, `SEARCHMUSE_*` env-var overrides, `ConfigurationError` paths.
- `test_logging_setup.py` — Handler attachment, idempotent reconfiguration, optional file handler creation.
- `test_i18n.py` — Translation lookup `t(...)` and language fallback.
- `test_keyring_store.py` — Optional `keyring` integration via mocks.
- `test_api_key_resolver.py` — Resolution order: explicit config → env var → keyring.
- `test_ollama_client.py` — Low-level Ollama HTTP client behaviour.

**Adapters (`tests/unit/adapters/`):**
- `test_httpx_scraper.py` — `HttpxScraperAdapter` happy path, error translation, `scrape_many`, robots.txt, rate limiting, idempotent `close`. Uses `respx` and `unittest.mock.patch` on `asyncio.sleep`.
- `test_playwright_scraper.py` — Playwright adapter behaviour with mocked browser context.
- `test_duckduckgo_search.py` — `DuckDuckGoSearchAdapter` result mapping with mocked `ddgs` client.
- `test_trafilatura_extractor.py` — Content extraction success and `ContentExtractionError` paths.
- `test_base_adapter.py` — Shared `BaseLLMAdapter` template-method logic (prompt construction, parsing).
- `test_ollama_adapter.py` — `OllamaLLMAdapter._chat` happy path and `LLMConnectionError` / `LLMResponseError` translation.
- `test_claude_adapter.py`, `test_openai_adapter.py`, `test_gemini_adapter.py` — Provider-specific `_chat` implementations with their SDKs mocked.
- `test_llm_factory.py` — `create_llm_adapter(...)` mapping `provider → adapter class` and unknown-provider error.
- `test_llm_helpers.py`, `test_llm_defaults.py` — Prompt/json parsing helpers and default model/temperature tables.
- `test_markdown_renderer.py`, `test_json_renderer.py`, `test_plain_renderer.py` — Output formatting for `SearchResult` rendering.
- `test_renderer_factory.py` — `create_renderer(format_name)` mapping and `ValueError` on unknown formats.
- `test_sqlite_repository.py` — `aiosqlite` source repository CRUD against `:memory:`.
- `test_sqlite_chat_repository.py` — Chat session/message persistence against `:memory:`.

**CLI (`tests/unit/cli/`):**
- `test_commands.py` — Typer `search` and `config` commands; env-var forwarding from CLI flags.
- `test_container.py` — `build_container` wires ports → adapters correctly.
- `test_display.py` — `Display` rendering and quiet mode.
- `test_interactive.py`, `test_interactive_chat.py` — Interactive REPL and chat session loops.
- `test_ollama_commands.py` — `ollama` subcommands (list/pull/etc.).

## Test Structure

Tests are organised into `class Test<Behaviour>` groups, with one assertion concept per `test_*` method. From `tests/unit/adapters/test_httpx_scraper.py`:

```python
class TestScrapeSuccess:
    """scrape must return a well-formed ScrapedPage on a successful 200 response."""

    @respx.mock
    async def test_returns_scraped_page_instance(self, adapter: HttpxScraperAdapter) -> None:
        respx.get("https://example.com/page").mock(
            return_value=httpx.Response(200, text="<html>Hello</html>")
        )
        page = await adapter.scrape("https://example.com/page")
        assert isinstance(page, ScrapedPage)
```

Patterns observed:
- One assertion per test (split rather than combined).
- Each test class has a docstring describing the contract it pins down.
- Section banners (`# ---...---`) separate test groups inside a file.
- Domain-level tests under `tests/unit/domain/` are plain `def test_*` functions (see `tests/unit/domain/test_validators.py`).

## Fixtures

**Global fixtures** live in `tests/conftest.py` and return frozen domain objects ready for use:

```python
@pytest.fixture()
def sample_query() -> SearchQuery:
    return SearchQuery(
        query_id=_short_id(),
        raw_text="  What is quantum entanglement?  ",
        normalized_text="What is quantum entanglement?",
        language="en",
        created_at=_now(),
    )
```

Conventions:
- Fixtures named `sample_<entity>` for domain objects, `test_config` for the aggregate config.
- Internal helpers `_short_id()` and `_now()` keep IDs and timestamps consistent.
- Fixtures depend on each other through parameter injection (e.g. `sample_citation(sample_source)`).

**Local fixtures** live at the top of each test file, often as module-level constants for static config plus `@pytest.fixture` factories for stateful adapters (see `BASE_CONFIG`, `ROBOTS_CONFIG`, `RATE_LIMIT_CONFIG` plus `adapter`, `robots_adapter`, `rate_limit_adapter` in `tests/unit/adapters/test_httpx_scraper.py`).

**Type-annotated fixtures:** even though `mypy` is relaxed for tests, fixtures and test parameters carry explicit type hints (`adapter: HttpxScraperAdapter`).

## Mocking

**HTTP mocking — `respx`:**
- Decorate the test with `@respx.mock`.
- Stub responses with `respx.get(url).mock(return_value=httpx.Response(200, text="..."))`.
- Stub errors with `respx.get(url).mock(side_effect=httpx.ConnectError("refused"))`.
- Assert call counts via the route object: `assert robots_route.call_count == 1`.

```python
@respx.mock
async def test_skips_failed_urls(self, adapter: HttpxScraperAdapter) -> None:
    respx.get("https://good.com/").mock(return_value=httpx.Response(200, text="good"))
    respx.get("https://bad.com/").mock(side_effect=httpx.ConnectError("refused"))
    pages = await adapter.scrape_many(("https://good.com/", "https://bad.com/"))
    assert len(pages) == 1
    assert pages[0].url == "https://good.com/"
```

**Sleep / time mocking** — `unittest.mock.patch` on the module reference to avoid touching the clock:

```python
with patch("searchmuse.adapters.scrapers.httpx_scraper.asyncio.sleep") as mock_sleep:
    mock_sleep.return_value = None
    await rate_limit_adapter.scrape("https://slow.com/page1")
```

**Port mocking** — `AsyncMock` / `MagicMock` from `unittest.mock` for `LLMPort`, `SearchPort`, `ScraperPort`, etc. (see `tests/unit/application/test_search_orchestrator.py`).

**Storage** — sqlite repositories are tested against the in-memory database (`db_path=":memory:"`, as already used in `test_config` fixture in `tests/conftest.py`); no temp-file fixtures required.

**Exception assertions** — `pytest.raises(...)` with `exc_info` and attribute checks:

```python
with pytest.raises(RequestTimeoutError) as exc_info:
    await adapter.scrape("https://example.com/slow")
assert exc_info.value.url == "https://example.com/slow"
```

**What NOT to mock:**
- The domain layer — frozen dataclasses, enums, validators are exercised with real instances.
- The configuration dataclasses — build a real `SearchMuseConfig` (see `test_config` fixture).

## Coverage

Configured in `pyproject.toml`:

```toml
[tool.coverage.run]
source = ["searchmuse"]
branch = true

[tool.coverage.report]
fail_under = 80
show_missing = true
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "if __name__ == .__main__.",
    "@overload",
    "\\.\\.\\.",
]
```

- **Threshold:** `fail_under = 80` — `pytest --cov` fails CI under 80%.
- **Branch coverage enabled** (`branch = true`), so both legs of every `if`/`except` are required.
- **Exclusions:** `TYPE_CHECKING` blocks, `__main__` guards, `@overload` stubs, and protocol `...` bodies are not counted (matches the heavy use of `TYPE_CHECKING` imports in the source).
- View an HTML report with `pytest --cov=searchmuse --cov-report=html` (output in `htmlcov/`).

## Markers

Declared under `[tool.pytest.ini_options] markers`:

- `slow` — long-running tests; deselected by default in fast loops with `-m "not slow"`.
- `integration` — tests that hit external services (e.g. real Ollama/Claude/OpenAI); excluded from the default unit-test matrix.

`--strict-markers` is enabled, so any undeclared marker fails the run — declare new markers in `pyproject.toml` before using them.

## Adding a New Test for a New Adapter

When introducing, e.g., a new scraper or LLM adapter, follow the conventions observed in `tests/unit/adapters/test_httpx_scraper.py`:

1. **Create the file** `tests/unit/adapters/test_<adapter>.py` mirroring the source path (`src/searchmuse/adapters/<sub>/<adapter>.py`).
2. **Module docstring** stating which adapter is under test and that no real I/O happens.
3. **Imports**: `from __future__ import annotations`, stdlib, third-party (`httpx`, `pytest`, `respx`), then `searchmuse.*` symbols (config dataclass, domain errors, domain models, the adapter class).
4. **Module-level config constants** (`BASE_CONFIG = ScrapingConfig(...)`) using real frozen dataclasses, not mocks.
5. **`@pytest.fixture` factories** returning a fresh adapter per test (e.g. `def adapter() -> MyAdapter: return MyAdapter(config=BASE_CONFIG)`).
6. **Group tests in `class Test<Behaviour>:`** with section banners separating concerns: `can_handle`, happy path, error translation, bulk operations, idempotency of `close()`, etc.
7. **Use `@respx.mock` for HTTP**, `AsyncMock` for cross-port collaborators, and `patch("module.path.asyncio.sleep")` to avoid real waits.
8. **One assertion per test method**; assert both the success type *and* the domain attributes (`page.url`, `exc_info.value.url`, etc.).
9. **Cover the error contract** declared in the adapter's `Raises:` docstring (e.g. `LLMConnectionError`, `LLMResponseError`, `ScrapingError`, `RequestTimeoutError`).
10. **Keep tests under the 80% branch-coverage budget** — exercise both `if respect_robots_txt` legs, both `try/except` branches, empty inputs, and the `close()` idempotency path.

If the adapter is async (it should be), no `@pytest.mark.asyncio` is needed — `asyncio_mode = "auto"` handles it.

If the new test is intentionally slow or requires a real external service, decorate it with `@pytest.mark.slow` or `@pytest.mark.integration` and document the trigger command in the file's module docstring.

---

*Testing analysis: 2026-05-18*
