# Codebase Structure

**Analysis Date:** 2026-05-18

## Directory Layout

```
WebScraping/
├── config/                                 # Bundled default configuration
│   └── default.yaml                        # Loaded first by infrastructure/config.py
├── docs/                                   # MkDocs sources (Material theme)
│   ├── index.md
│   ├── 001_functional/                     # English functional docs (vision, use cases, roadmap, ...)
│   ├── 002_technical/                      # English technical docs (architecture, components, data flow, ...)
│   └── 003_it/                             # Italian translation root
│       ├── 000_index.md
│       ├── 001_functional/
│       └── 002_technical/
├── src/
│   └── searchmuse/                         # Single installable package (hatchling)
│       ├── __init__.py
│       ├── __main__.py                     # `python -m searchmuse` entry point
│       ├── version.py                      # Single source of truth for __version__
│       ├── domain/                         # Pure domain layer (no I/O)
│       │   ├── __init__.py                 # Re-exports models, enums, errors
│       │   ├── models.py                   # Frozen dataclasses: SearchQuery, SearchState, Source, ...
│       │   ├── enums.py                    # StrEnums: SearchPhase, RelevanceScore, ContentType, SourceStatus
│       │   ├── errors.py                   # SearchMuseError hierarchy
│       │   └── validators.py               # validate_query
│       ├── ports/                          # Abstract Protocols (one per outbound capability)
│       │   ├── __init__.py                 # Re-exports every port
│       │   ├── llm_port.py                 # LLMPort
│       │   ├── search_port.py              # SearchPort
│       │   ├── scraper_port.py             # ScraperPort
│       │   ├── content_extractor_port.py   # ContentExtractorPort
│       │   ├── result_renderer_port.py     # ResultRendererPort
│       │   ├── source_repository_port.py   # SourceRepositoryPort
│       │   └── chat_repository_port.py     # ChatRepositoryPort
│       ├── application/                    # Use case orchestration
│       │   ├── __init__.py
│       │   ├── search_orchestrator.py      # SearchOrchestrator (the only use case)
│       │   └── progress.py                 # ProgressEvent, ProgressCallback, NullProgress
│       ├── adapters/                       # Concrete port implementations
│       │   ├── __init__.py
│       │   ├── llm/
│       │   │   ├── __init__.py             # Exports create_llm_adapter
│       │   │   ├── _base.py                # BaseLLMAdapter shared logic
│       │   │   ├── _defaults.py            # PROVIDER_DEFAULTS, SUPPORTED_PROVIDERS
│       │   │   ├── _helpers.py
│       │   │   ├── _factory.py             # create_llm_adapter(config.llm)
│       │   │   ├── prompts.py              # Prompt templates
│       │   │   ├── ollama_adapter.py       # OllamaLLMAdapter (default)
│       │   │   ├── claude_adapter.py       # ClaudeLLMAdapter (extra: claude)
│       │   │   ├── openai_adapter.py       # OpenAILLMAdapter (extra: openai)
│       │   │   └── gemini_adapter.py       # GeminiLLMAdapter (extra: gemini)
│       │   ├── scrapers/
│       │   │   ├── __init__.py
│       │   │   ├── duckduckgo_search.py    # DuckDuckGoSearchAdapter (SearchPort)
│       │   │   ├── httpx_scraper.py        # HttpxScraperAdapter (ScraperPort, default)
│       │   │   └── playwright_scraper.py   # PlaywrightScraperAdapter (opt-in)
│       │   ├── extractors/
│       │   │   ├── __init__.py
│       │   │   └── trafilatura_extractor.py# TrafilaturaExtractorAdapter
│       │   ├── repositories/
│       │   │   ├── __init__.py
│       │   │   ├── sqlite_repository.py    # SqliteRepositoryAdapter (sources)
│       │   │   └── sqlite_chat_repository.py # SqliteChatRepositoryAdapter
│       │   └── renderers/
│       │       ├── __init__.py
│       │       ├── factory.py              # create_renderer(format_name)
│       │       ├── markdown_renderer.py    # MarkdownRendererAdapter (default)
│       │       ├── json_renderer.py        # JsonRendererAdapter
│       │       └── plain_renderer.py       # PlainRendererAdapter
│       ├── infrastructure/                 # Cross-cutting technical services
│       │   ├── __init__.py
│       │   ├── config.py                   # SearchMuseConfig + load_config
│       │   ├── logging_setup.py            # setup_logging(LoggingConfig)
│       │   ├── i18n.py                     # set_language, t(key, **kwargs)
│       │   ├── api_key_resolver.py         # resolve_api_key(provider, fallback)
│       │   ├── keyring_store.py            # Optional keyring backend
│       │   └── ollama_client.py            # Low-level Ollama HTTP helper
│       └── cli/                            # Typer driver / composition root
│           ├── __init__.py                 # `app` (Typer); exposed as `searchmuse` script
│           ├── commands.py                 # run_search, config subcommands
│           ├── container.py                # Container, build_container (DI)
│           ├── display.py                  # Rich-based UI + progress callback
│           ├── interactive.py              # InteractiveSession REPL
│           └── ollama_commands.py          # `searchmuse ollama …` subcommands
├── tests/
│   ├── __init__.py
│   ├── conftest.py                         # Shared fixtures
│   └── unit/
│       ├── __init__.py
│       ├── domain/                         # test_models, test_enums, test_validators, test_chat_models
│       ├── application/                    # test_search_orchestrator, test_orchestrator_context, test_progress
│       ├── infrastructure/                 # test_config, test_i18n, test_keyring_store, test_logging_setup, test_api_key_resolver, test_ollama_client
│       ├── adapters/                       # one test_<adapter>.py per concrete adapter + factory/helpers
│       └── cli/                            # test_commands, test_container, test_display, test_interactive, test_interactive_chat, test_ollama_commands
├── pyproject.toml                          # Build (hatchling), deps, scripts, ruff, mypy, pytest, coverage
├── mkdocs.yml                              # Docs site configuration (Material + Mermaid)
├── Dockerfile                              # Container image build
├── README.md / README.it.md                # English / Italian readmes
├── CHANGELOG.md / CONTRIBUTING.md / CODE_OF_CONDUCT.md / SECURITY.md / LICENSE
└── site/                                   # Built docs output (generated; not committed source)
```

(Caches `.venv/`, `.git/`, `.mypy_cache/`, `.pytest_cache/`, `.ruff_cache/`, `__pycache__/` and the generated `site/` tree are excluded from this view.)

## Directory Purposes

**`src/searchmuse/domain/`**
- Purpose: Pure business types and rules. No I/O, no third-party deps beyond stdlib.
- Contains: Frozen dataclasses (`models.py`), `StrEnum`s (`enums.py`), exception hierarchy (`errors.py`), validators (`validators.py`).
- Key files: `src/searchmuse/domain/models.py`, `src/searchmuse/domain/errors.py`.

**`src/searchmuse/ports/`**
- Purpose: Abstract `typing.Protocol` contracts the application requires from the outside world.
- Contains: One module per port, all `@runtime_checkable`.
- Key files: `src/searchmuse/ports/llm_port.py`, `src/searchmuse/ports/scraper_port.py`.

**`src/searchmuse/application/`**
- Purpose: Use case orchestration; depends only on `domain/` and `ports/` (plus `infrastructure/i18n` for translated messages).
- Key files: `src/searchmuse/application/search_orchestrator.py`, `src/searchmuse/application/progress.py`.

**`src/searchmuse/adapters/`**
- Purpose: Concrete port implementations, one subpackage per kind (`llm/`, `scrapers/`, `extractors/`, `repositories/`, `renderers/`).
- Key files: `src/searchmuse/adapters/llm/_factory.py`, `src/searchmuse/adapters/renderers/factory.py`.

**`src/searchmuse/infrastructure/`**
- Purpose: Cross-cutting technical services (config loading, logging, i18n, keyring, ollama HTTP).
- Key files: `src/searchmuse/infrastructure/config.py`, `src/searchmuse/infrastructure/api_key_resolver.py`.

**`src/searchmuse/cli/`**
- Purpose: Typer driver and composition root; the only place that wires concrete adapters to ports.
- Key files: `src/searchmuse/cli/__init__.py` (the `app` object), `src/searchmuse/cli/container.py` (DI), `src/searchmuse/cli/commands.py`.

**`tests/unit/`**
- Purpose: Mirrors `src/searchmuse/` exactly. One `test_<module>.py` per source module.
- Configured by `pyproject.toml` `[tool.pytest.ini_options]` with `asyncio_mode = "auto"` and `pythonpath = ["src"]`.

**`config/`**
- Purpose: Bundled default YAML loaded first by `load_config`.
- Files: `config/default.yaml`.

**`docs/`**
- Purpose: MkDocs Material source. Split into `001_functional/`, `002_technical/`, and `003_it/` (Italian mirror). The built site lives in `site/` (generated).

## Key File Locations

**Entry Points:**
- `src/searchmuse/cli/__init__.py` — Typer `app`; exposed by `pyproject.toml:70` as `searchmuse = "searchmuse.cli:app"`.
- `src/searchmuse/__main__.py` — `python -m searchmuse`.

**Configuration:**
- `config/default.yaml` — bundled defaults.
- `src/searchmuse/infrastructure/config.py` — `load_config(path)` and frozen `SearchMuseConfig`.
- `pyproject.toml` — build, deps, ruff, mypy, pytest, coverage.
- `mkdocs.yml` — docs site.

**Core Logic:**
- `src/searchmuse/application/search_orchestrator.py` — the iterative search use case.
- `src/searchmuse/domain/models.py` — immutable state primitives.
- `src/searchmuse/cli/container.py` — composition root.

**Testing:**
- `tests/conftest.py` — shared fixtures.
- `tests/unit/<layer>/test_<module>.py` — mirrors source layout.

## Naming Conventions

**Modules / files:**
- `snake_case.py`, one public class per module where practical.
- Adapter modules end in `_adapter.py` for LLM providers (`ollama_adapter.py`, `claude_adapter.py`), or describe the backend (`httpx_scraper.py`, `duckduckgo_search.py`, `sqlite_repository.py`, `trafilatura_extractor.py`).
- Renderer modules end in `_renderer.py`.
- Port modules end in `_port.py` and live exclusively in `src/searchmuse/ports/`.
- Private helpers inside a subpackage use a leading underscore (`_base.py`, `_defaults.py`, `_factory.py`, `_helpers.py`).
- Test files are `test_<source_module>.py` and mirror the source path one-for-one.

**Classes:**
- `PascalCase`.
- Port protocols end in `Port` (e.g. `LLMPort`, `ScraperPort`).
- Concrete adapters end in `Adapter` (e.g. `OllamaLLMAdapter`, `HttpxScraperAdapter`, `SqliteRepositoryAdapter`, `MarkdownRendererAdapter`).
- Domain value objects are noun-only (`SearchState`, `SearchResult`, `Source`, `Citation`).
- Errors end in `Error` and inherit from `SearchMuseError`.
- Enums are `StrEnum` subclasses with `UPPER_SNAKE_CASE` members (see `src/searchmuse/domain/enums.py`).

**Functions / variables:**
- `snake_case`; async coroutines are not prefixed with `async_` — async-ness is conveyed by the keyword and `await` usage.
- Factory functions are `create_<thing>` (`create_llm_adapter`, `create_renderer`) or `build_<thing>` (`build_container`).
- Immutable-state mutators on dataclasses are named `with_<field>` and return a new instance (e.g. `SearchState.with_phase`, `ChatSession.with_message`).
- Private module-level helpers and constants use a leading underscore (`_short_id`, `_now`, `_ENV_PREFIX`).

**Type style:**
- `from __future__ import annotations` everywhere.
- `tuple[...]` over `list[...]` for any field that crosses a layer boundary.
- Domain imports inside ports/adapters are guarded by `if TYPE_CHECKING:` to keep the runtime import graph minimal.
- Ruff target `py311`; mypy strict.

## Where to Add New Code

**New adapter (e.g. a Bing search backend):**
1. Pick the right subpackage under `src/searchmuse/adapters/` — for a search engine it would be `src/searchmuse/adapters/scrapers/bing_search.py`.
2. Implement the corresponding port (`SearchPort` from `src/searchmuse/ports/search_port.py`) as a plain class named `BingSearchAdapter`. Do **not** inherit from the Protocol; rely on structural typing.
3. Translate backend exceptions into the appropriate `SearchMuseError` subclass from `src/searchmuse/domain/errors.py`.
4. If the adapter brings a new third-party dependency, declare it as an optional extra in `pyproject.toml` (`[project.optional-dependencies]`) and import it lazily inside the adapter.
5. Wire it in the composition root `src/searchmuse/cli/container.py` (or in `src/searchmuse/adapters/llm/_factory.py` for a new LLM provider — also add an entry to `SUPPORTED_PROVIDERS` / `PROVIDER_DEFAULTS` in `src/searchmuse/adapters/llm/_defaults.py`).
6. Add unit tests under `tests/unit/adapters/test_bing_search.py`, following the patterns in `tests/unit/adapters/test_duckduckgo_search.py`.

**New renderer:**
1. Add `src/searchmuse/adapters/renderers/<format>_renderer.py` implementing `ResultRendererPort` (`render`, `format_name`).
2. Register it in `src/searchmuse/adapters/renderers/factory.py: create_renderer`.
3. Add `tests/unit/adapters/test_<format>_renderer.py`.

**New domain entity / value object:**
1. Add the frozen dataclass to `src/searchmuse/domain/models.py` (or split into a new module under `src/searchmuse/domain/` if the file grows past ~400 lines).
2. Use `@dataclasses.dataclass(frozen=True, slots=True)`, `tuple[...]` for collections, and provide `with_*` helpers for state evolution.
3. Re-export it from `src/searchmuse/domain/__init__.py`.
4. Add corresponding error subclasses to `src/searchmuse/domain/errors.py` if needed.
5. Add unit tests in `tests/unit/domain/test_<area>.py`.

**New port / capability:**
1. Add `src/searchmuse/ports/<name>_port.py` with a `@runtime_checkable` `Protocol` named `<Name>Port`.
2. Guard all `domain` imports behind `TYPE_CHECKING`.
3. Re-export from `src/searchmuse/ports/__init__.py`.
4. Add at least one concrete adapter under `src/searchmuse/adapters/<area>/` and wire it in `Container.__init__`.

**New use case / application service:**
1. Create `src/searchmuse/application/<use_case>.py`.
2. Depend only on ports and domain (plus `infrastructure.i18n` for user-facing strings).
3. Take ports via constructor injection; never instantiate adapters inside `application/`.
4. Add tests in `tests/unit/application/test_<use_case>.py`.

**New CLI subcommand:**
1. Add the command function to `src/searchmuse/cli/commands.py` (or to `ollama_commands.py` for ollama-specific operations).
2. Register it on the `app` Typer instance in `src/searchmuse/cli/__init__.py` (use `@app.command(...)` or `app.add_typer(...)` for a group).
3. Resolve dependencies through `build_container` — never instantiate adapters directly inside a command.
4. Map domain errors to localized panels via `Display.show_error` + `t(...)`.
5. Add CLI tests in `tests/unit/cli/test_commands.py` (or a dedicated file for a new subcommand group).

**New configuration field:**
1. Add the field to the appropriate frozen dataclass in `src/searchmuse/infrastructure/config.py`.
2. Add the default value to `config/default.yaml`.
3. Ensure the env-var mapping (`SEARCHMUSE_<SECTION>_<FIELD>`) works through the existing `load_config` overlay.
4. Update `tests/unit/infrastructure/test_config.py`.

**New tests (general rule):**
- Mirror source path: `src/searchmuse/<layer>/<module>.py` → `tests/unit/<layer>/test_<module>.py`.
- Place shared fixtures in `tests/conftest.py`.
- Async tests need no decorator — `asyncio_mode = "auto"` (`pyproject.toml:135`).
- Aim for the project-wide `fail_under = 80` coverage gate (`pyproject.toml:151`).

## Special Directories

**`site/`**
- Purpose: Built MkDocs output.
- Generated: Yes (by `mkdocs build`).
- Committed: Present in the working tree but should be regenerated; do not edit by hand.

**`.venv/`, `.mypy_cache/`, `.pytest_cache/`, `.ruff_cache/`**
- Purpose: Local virtual env and tool caches.
- Generated: Yes.
- Committed: No (covered by `.gitignore`).

**`.github/workflows/`**
- Purpose: GitHub Actions CI definitions.
- Committed: Yes.

**`.planning/codebase/`**
- Purpose: GSD codebase map outputs (this document and siblings).
- Generated: Yes (by `/gsd:map-codebase`).

---

*Structure analysis: 2026-05-18*
