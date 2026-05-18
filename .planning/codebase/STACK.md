# Technology Stack

**Analysis Date:** 2026-05-18

## Languages

**Primary:**
- Python `>=3.11` — declared in `pyproject.toml` (`requires-python`). All source under `src/searchmuse/` is type-annotated (PEP 561, `Typing :: Typed` classifier).

**Supported runtimes (CI matrix):**
- Python 3.11, 3.12, 3.13 — see `.github/workflows/ci.yml` (`test` job `matrix.python-version`).

**Secondary:**
- YAML — configuration (`config/default.yaml`, `mkdocs.yml`).
- Dockerfile — container packaging (`Dockerfile`, multi-stage).
- Markdown — documentation under `docs/` (English + Italian).

## Runtime

**Environment:**
- CPython 3.11–3.13. Docker image uses `python:3.12-slim` for both build and runtime stages (`Dockerfile` lines 1, 13).
- Asyncio-first: adapters use `httpx.AsyncClient`, `aiosqlite`, `ollama.AsyncClient`, `playwright.async_api`, `asyncio.to_thread` wrappers.

**Package Manager:**
- `pip` (no lockfile committed — no `poetry.lock`, `uv.lock`, `requirements.txt`). Dependencies pinned only by minimum version in `pyproject.toml`.

## Frameworks

**CLI:**
- `typer >=0.12` — command framework (`src/searchmuse/cli/__init__.py`, `cli/commands.py`, `cli/ollama_commands.py`).
- `rich >=13.0` — terminal rendering, progress bars (`src/searchmuse/cli/display.py`, `application/progress.py`).

**Async HTTP:**
- `httpx[http2] >=0.27` — both async (scraping) and sync (Ollama REST probe) usage.

**Browser Automation:**
- `playwright >=1.45` — headless Chromium for JS-rendered pages (`src/searchmuse/adapters/scrapers/playwright_scraper.py`). Installed in Docker via `playwright install chromium --with-deps` (`Dockerfile` line 29).

**Content Extraction:**
- `trafilatura >=1.12` — primary extractor.
- `readability-lxml >=0.8` — fallback extractor.
- `beautifulsoup4 >=4.12` — HTML cleanup after readability fallback.

**Search:**
- `duckduckgo-search >=8.0` — web search backend.

**LLM Clients:**
- `ollama >=0.4` — local LLM (default, required).
- Optional extras: `anthropic >=0.39` (claude), `openai >=1.50` (openai), `google-genai >=1.0` (gemini).

**Persistence:**
- `aiosqlite >=0.20` — async SQLite (sources + chat sessions).

**Config / Serialisation:**
- `pyyaml >=6.0` — YAML config loader (`src/searchmuse/infrastructure/config.py`).

## Build / Packaging

**Build Backend:**
- `hatchling` (PEP 517). Configured in `pyproject.toml` `[build-system]` and `[tool.hatch.*]`.
- Version is dynamic, sourced from `src/searchmuse/version.py` (`__version__ = "0.1.0"`).
- Wheel target: `packages = ["src/searchmuse"]`.

**Entry Point:**
- Console script `searchmuse = "searchmuse.cli:app"` (`pyproject.toml` `[project.scripts]`).
- Module entry: `python -m searchmuse` via `src/searchmuse/__main__.py`.

**Optional Extras:**
- `[claude]`, `[openai]`, `[gemini]`, `[keyring]`, `[all-providers]`, `[docs]`, `[dev]`.

## Linting / Formatting

**Ruff** `>=0.6` (dev extra):
- Target: `py311`, line length 100, `src = ["src", "tests"]`.
- Lint rule sets: `E`, `W`, `F`, `I` (isort), `N` (pep8-naming), `UP` (pyupgrade), `B` (bugbear), `SIM`, `TCH` (type-checking), `RUF`.
- Ignores: `E501` (handled by formatter), `B008` (Typer default-arg pattern).
- isort first-party: `searchmuse`.
- CI: `ruff check src/ tests/` in `.github/workflows/ci.yml` `lint` job.

## Type Checking

**mypy** `>=1.11` (dev extra) — strict mode:
- `strict = true`, `disallow_untyped_defs`, `disallow_incomplete_defs`, `no_implicit_optional`, `warn_redundant_casts`, `warn_unused_ignores`.
- Per-module overrides: tests allow untyped defs; optional SDKs (`anthropic`, `openai`, `google`, `google.genai`, `keyring`) have `ignore_missing_imports = true` so they don't break type-checking when extras aren't installed.
- CI: `mypy src/searchmuse/` in `.github/workflows/ci.yml` `type-check` job.

## Test Stack

- `pytest >=8.0` — runner. Config in `pyproject.toml` `[tool.pytest.ini_options]`.
  - `testpaths = ["tests"]`, `pythonpath = ["src"]`, `asyncio_mode = "auto"`.
  - `addopts = ["--strict-markers", "--tb=short", "-q"]`.
  - Custom markers: `slow`, `integration`.
- `pytest-asyncio >=0.24` — async test support (auto mode means every coroutine test is auto-marked).
- `pytest-cov >=5.0` — coverage. Configured under `[tool.coverage.*]`: `source = ["searchmuse"]`, `branch = true`, `fail_under = 80`.
- `respx >=0.21` — httpx mocking for adapter tests.
- `types-PyYAML >=6.0` — type stubs.
- Tests live under `tests/` and are excluded from strict typing.

## Docs Stack

- `mkdocs-material >=9.5` — theme + site generator. Configured in `mkdocs.yml`.
- `mkdocs-mermaid2-plugin >=1.1` — listed in `[project.optional-dependencies.docs]` (note: `mkdocs.yml` `plugins` only lists `search`; Mermaid is rendered via injected `extra_javascript` pointing at `https://unpkg.com/mermaid@11/dist/mermaid.min.js`).
- Markdown extensions: `pymdownx.highlight`, `superfences` (with mermaid custom fence), `tabbed`, `emoji`, `inlinehilite`, `mark`, `keys`, `smartsymbols`, `admonition`, `details`, `attr_list`, `md_in_html`, `def_list`, `footnotes`, `abbr`, `tables`, `toc` (permalinks).
- Bilingual nav (English + Italiano) defined in `mkdocs.yml` `nav:`.
- Theme: Material with `deep purple` / `amber` palette, dark/light toggle, instant navigation, code copy/annotate.

## CI/CD

All workflows under `.github/workflows/`:

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `ci.yml` | push / PR on `master` | Three jobs: `lint` (ruff), `type-check` (mypy), `test` (pytest matrix 3.11/3.12/3.13 with coverage). |
| `docs.yml` | push to `master` touching `docs/**`, `mkdocs.yml`, `pyproject.toml`, workflow itself; or `workflow_dispatch` | Build `mkdocs build --strict --clean` and deploy to GitHub Pages via `actions/upload-pages-artifact@v3` + `actions/deploy-pages@v4`. Concurrency group `pages` cancels in-progress runs. |
| `docs-check.yml` | PR on `master` touching docs paths | Strict mkdocs build, uploads `docs-preview` artifact (7-day retention). |

**GitHub Actions used:** `actions/checkout@v4`, `actions/setup-python@v5` (pip cache keyed on `pyproject.toml`), `actions/upload-pages-artifact@v3`, `actions/deploy-pages@v4`, `actions/upload-artifact@v4`.

**Permissions (docs.yml deploy):** `contents: read`, `pages: write`, `id-token: write` (OIDC for Pages).

## Runtime / Dev Tooling

- `.venv/` — local virtual environment (gitignored).
- `.ruff_cache/`, `.mypy_cache/`, `.pytest_cache/` — tool caches (gitignored).
- `.coverage` — local coverage artefact (present at repo root).
- `Dockerfile` — multi-stage: `python:3.12-slim` builder produces wheel via `python -m build`; runtime stage installs the wheel, adds Playwright system libs (`libnss3`, `libatk-bridge2.0-0`, `libdrm2`, `libxcomposite1`, `libxdamage1`, `libxrandr2`, `libgbm1`, `libasound2`, `libpango-1.0-0`, `libcairo2`, `libatspi2.0-0`, `libxshmfence1`), installs Chromium, and sets `ENTRYPOINT ["searchmuse"]`.
- `.dockerignore` — present (excludes build artefacts from Docker context).

## Configuration Entry Points

| File | Role |
|------|------|
| `pyproject.toml` | Build, dependencies, extras, ruff, mypy, pytest, coverage config. |
| `mkdocs.yml` | Documentation site definition. |
| `config/default.yaml` | Bundled application defaults (LLM, search, scraping, extraction, storage, output, logging). Loaded by `src/searchmuse/infrastructure/config.py` from `_DEFAULT_CONFIG_PATH = Path(__file__).parent.parent.parent.parent / "config" / "default.yaml"`. |
| `.env.example` | Template for runtime environment variables; copy to `.env`. Lists `SEARCHMUSE_LLM_BASE_URL`, `SEARCHMUSE_LLM_MODEL`, `SEARCHMUSE_MAX_ITERATIONS`, `SEARCHMUSE_MIN_SOURCES`, `SEARCHMUSE_REQUEST_DELAY`, `SEARCHMUSE_REQUEST_TIMEOUT`, `SEARCHMUSE_DB_PATH`, `SEARCHMUSE_LOG_LEVEL`. |
| `Dockerfile` | Container build recipe (multi-stage, Playwright-ready). |
| `src/searchmuse/infrastructure/config.py` | Loader: layers `config/default.yaml` → user-supplied YAML → `SEARCHMUSE_*` env vars (descending → ascending priority). Produces frozen dataclasses (`LLMConfig`, `SearchConfig`, `ScrapingConfig`, `ExtractionConfig`, `StorageConfig`, `OutputConfig`, `LoggingConfig`, `SearchMuseConfig`). |

## Platform Requirements

**Development:**
- Python 3.11+ with `pip` and `venv`.
- Playwright system dependencies for Chromium (only when `scraping.use_playwright: true` — see `config/default.yaml` line 49).
- Optional: system keyring backend (GNOME Keyring / macOS Keychain / Windows Credential Locker) when using `[keyring]` extra.

**Production:**
- Containerised via `Dockerfile` (target: `python:3.12-slim`, ENTRYPOINT `searchmuse`).
- Local Ollama server reachable at `SEARCHMUSE_LLM_BASE_URL` (default `http://localhost:11434`) when using the default `ollama` provider.

---

*Stack analysis: 2026-05-18*
