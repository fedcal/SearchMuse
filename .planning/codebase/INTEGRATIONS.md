# External Integrations

**Analysis Date:** 2026-05-18

SearchMuse is a CLI research assistant; all outbound integrations go through hexagonal adapters under `src/searchmuse/adapters/` and `src/searchmuse/infrastructure/`. The domain layer never imports a third-party client directly.

## LLM Providers

### Ollama (default, local)

- **Files:**
  - `src/searchmuse/adapters/llm/ollama_adapter.py` — async chat via `ollama.AsyncClient` (uses the official `ollama` package).
  - `src/searchmuse/infrastructure/ollama_client.py` — sync `httpx` calls to `GET /api/tags` and pull endpoints; used by Typer CLI commands (`src/searchmuse/cli/ollama_commands.py`) for reachability checks, model listing, and pull-with-progress.
- **Config knobs (`config/default.yaml` `llm:` block, defaults from `src/searchmuse/adapters/llm/_defaults.py`):**
  - `provider: "ollama"`, `base_url: "http://localhost:11434"`, `model: "mistral"`.
  - `strategy_temperature`, `assessment_temperature`, `synthesis_temperature`, `max_tokens`, `timeout`.
  - Env overrides: `SEARCHMUSE_LLM_BASE_URL`, `SEARCHMUSE_LLM_MODEL`.
- **Auth:** None — `requires_api_key = False` in `PROVIDER_DEFAULTS["ollama"]`.
- **Failure mode:** Raises `LLMConnectionError` (server unreachable) or `LLMResponseError` (unparseable JSON) — defined in `src/searchmuse/domain/errors.py`. `ollama_client.is_reachable()` returns `False` on `httpx.HTTPError`/`OSError` instead of raising.

### Anthropic Claude (optional extra: `searchmuse[claude]`)

- **File:** `src/searchmuse/adapters/llm/claude_adapter.py` — uses `anthropic.AsyncAnthropic`, lazy-imported inside `__init__` so the dep is only required when selected.
- **Endpoint:** Messages API at `https://api.anthropic.com` (`PROVIDER_DEFAULTS["claude"].base_url`).
- **Default model:** `claude-sonnet-4-6` (`src/searchmuse/adapters/llm/_defaults.py` line 28).
- **Auth:** API key resolved by `src/searchmuse/infrastructure/api_key_resolver.py` priority chain: `SEARCHMUSE_LLM_API_KEY` → `ANTHROPIC_API_KEY` → system keyring → `llm.api_key` in YAML.
- **Retries:** `max_retries=0` (no SDK-level retries — caller controls).
- **Failure modes:**
  - `LLMAuthenticationError` ← `anthropic.AuthenticationError`.
  - `LLMConnectionError` ← `anthropic.APIConnectionError`, `APITimeoutError`, `APIStatusError`.
  - `LLMResponseError` ← unexpected response structure (`IndexError`/`AttributeError` on `response.content[0].text`).

### OpenAI (optional extra: `searchmuse[openai]`)

- **File:** `src/searchmuse/adapters/llm/openai_adapter.py` — uses `openai.AsyncOpenAI`, lazy-imported.
- **Endpoint:** Chat Completions API at `https://api.openai.com/v1` (`PROVIDER_DEFAULTS["openai"].base_url`).
- **Default model:** `gpt-4o`.
- **Auth:** API key via `api_key_resolver.resolve_api_key("openai", ...)`. Provider-specific env var: `OPENAI_API_KEY`.
- **Retries:** `max_retries=0`.
- **Failure modes:** Same mapping as Claude — `AuthenticationError` → `LLMAuthenticationError`; `APIConnectionError`/`APITimeoutError`/`APIStatusError` → `LLMConnectionError`; malformed `choices[0].message.content` → `LLMResponseError`.

### Google Gemini (optional extra: `searchmuse[gemini]`)

- **File:** `src/searchmuse/adapters/llm/gemini_adapter.py` — uses `google.genai.Client` (the new `google-genai` SDK), invoked via `client.aio.models.generate_content(...)`. Lazy-imported.
- **Endpoint:** `https://generativelanguage.googleapis.com` (`PROVIDER_DEFAULTS["gemini"].base_url`).
- **Default model:** `gemini-2.0-flash`.
- **Auth:** API key via `api_key_resolver.resolve_api_key("gemini", ...)`. Provider-specific env var: `GOOGLE_API_KEY`.
- **Failure modes:**
  - `LLMAuthenticationError` ← `genai.errors.ClientError` when error string contains `"api_key"`, `"401"`, or `"403"`.
  - `LLMConnectionError` ← other `ClientError` instances and any unexpected `Exception`.
  - `LLMResponseError` ← missing `response.text`.

### LLM provider selection

- Factory: `src/searchmuse/adapters/llm/_factory.py` dispatches on `config.llm.provider`. Only the selected provider's SDK is imported, allowing the base install to work without optional extras.
- Supported set: `frozenset({"ollama", "claude", "openai", "gemini"})` (`src/searchmuse/adapters/llm/_defaults.py` line 44).

## Web Search

### DuckDuckGo

- **File:** `src/searchmuse/adapters/scrapers/duckduckgo_search.py` — wraps synchronous `duckduckgo_search.DDGS.text()` inside `asyncio.to_thread` to avoid blocking the event loop. `DDGS()` is instantiated per call (stateless library).
- **Config knobs:** `max_results`, `region` (default `wt-wt`), `safesearch` (default `moderate`), `timelimit` (`d`/`w`/`m`/`y` or `None`), `language` (BCP-47 mapped to DDG region via `_LANGUAGE_TO_REGION` for `en/it/de/fr/es/pt/nl/ja/zh/ko/ru`).
- **Auth:** None — public scraping endpoint.
- **Failure mode:** All `DDGS` exceptions translated into `searchmuse.domain.errors.ScrapingError` to keep the domain insulated.
- **Output mapping:** Raw dicts → frozen `SearchHit` (url ← `href`, title, snippet ← `body`) in `_build_search_hit`.

## HTTP Scraping (page fetching)

### httpx-based scraper (default)

- **File:** `src/searchmuse/adapters/scrapers/httpx_scraper.py` — async fetcher using `httpx.AsyncClient` over HTTP/1.1 and HTTP/2 (`httpx[http2]` extra).
- **Features:**
  - Per-domain rate limiting via `asyncio.sleep` (`scraping.request_delay`).
  - Bounded concurrency via `asyncio.Semaphore` (`scraping.max_concurrent`).
  - Optional `robots.txt` compliance with in-memory cache (`urllib.robotparser`, 5 s timeout, `_ROBOTS_TXT_PATH = "/robots.txt"`).
  - Content-type detection mapping `text/html`, `application/xhtml+xml`, `application/pdf`, `application/json`, `text/plain` → `ContentType` enum.
  - Max page size enforced (`scraping.max_page_size`, default 5 MiB).
- **Auth:** None (public web fetch). User-Agent from `scraping.user_agent`.
- **Failure modes:** `RequestTimeoutError`, `RobotsTxtBlockedError`, `ScrapingError` (all in `src/searchmuse/domain/errors.py`).

### Playwright scraper (optional, JS pages)

- **File:** `src/searchmuse/adapters/scrapers/playwright_scraper.py` — headless Chromium via `playwright.async_api.async_playwright()`, browser launched lazily on first request.
- **Activation:** `scraping.use_playwright: true` in `config/default.yaml` (default `false`).
- **Features:** Per-domain rate limiting, `asyncio.Semaphore` concurrency, page size limit, idempotent cleanup.
- **System dependencies:** Installed in `Dockerfile` (libnss3, libatk-bridge2.0-0, libdrm2, libxcomposite1, libxdamage1, libxrandr2, libgbm1, libasound2, libpango-1.0-0, libcairo2, libatspi2.0-0, libxshmfence1) plus `playwright install chromium --with-deps`.
- **Failure modes:** `RequestTimeoutError`, `ScrapingError`.

### Content extractors

- **File:** `src/searchmuse/adapters/extractors/trafilatura_extractor.py`.
- **Primary path:** `trafilatura.extract()` for body, `trafilatura.extract_metadata()` for title/author/date.
- **Fallback path:** `readability.Document` distils the article HTML, then `bs4.BeautifulSoup` strips tags to plain text. Triggered when trafilatura returns empty.
- **Supported types:** `frozenset({ContentType.HTML, ContentType.PLAIN_TEXT})`.
- **Failure mode:** `ContentExtractionError` raised when post-extraction word count falls below `extraction.min_word_count` (default 50).
- **Auth:** None — purely local processing.

## Persistence

### SQLite via `aiosqlite`

Two repository adapters, one shared database file (path: `storage.db_path`, default `~/.searchmuse/searchmuse.db`, overridable via `SEARCHMUSE_DB_PATH`).

- **`src/searchmuse/adapters/repositories/sqlite_repository.py`** — sources store.
  - Table: `sources` (PK `source_id`, FKs by `session_id`/`content_id`, columns: `url`, `title`, `snippet`, `relevance_score`, `credibility_notes`, `author`, `accessed_at`).
  - Implements `SourceRepositoryPort` (`src/searchmuse/ports/source_repository_port.py`).
- **`src/searchmuse/adapters/repositories/sqlite_chat_repository.py`** — chat sessions and messages.
  - Tables: `chat_sessions` (`session_id` PK, `name`, `created_at`, `updated_at`), `chat_messages` (`message_id` PK, `session_id` FK → `chat_sessions`, `role`, `content`, …).
  - Implements `ChatRepositoryPort` (`src/searchmuse/ports/chat_repository_port.py`).
- **Connection lifecycle:** Both adapters create the connection and tables lazily via `_ensure_db()` on first call — construction stays synchronous and lightweight.
- **Auth:** Local file; no network. Directory is created on demand.
- **Failure mode:** All `aiosqlite` exceptions caught and re-raised as `searchmuse.domain.errors.StorageError` so the domain layer never sees the third-party exception type.

## Secrets

### System Keyring (optional extra: `searchmuse[keyring]`)

- **File:** `src/searchmuse/infrastructure/keyring_store.py` — wraps the `keyring` package with graceful degradation.
  - On `ImportError` during module load, `_HAS_KEYRING = False` and every public function returns `None` / silently no-ops.
  - Service name: `"searchmuse"`. Per-provider username: `f"searchmuse-{provider}-api-key"`.
  - Public API: `is_available()`, `get_api_key(provider)`, `store_api_key(provider, api_key)` (and corresponding delete in the rest of the module).
- **Backends:** GNOME Keyring, macOS Keychain, Windows Credential Locker (whatever `keyring` resolves at runtime).
- **CLI integration:** `src/searchmuse/cli/commands.py` imports `keyring_store` (line 227) to expose set/get commands for stored API keys.
- **Failure mode:** Any backend exception is caught and logged at DEBUG; functions return `None`/`False` to caller — never raises.

### API key resolution chain

- **File:** `src/searchmuse/infrastructure/api_key_resolver.py`.
- **Priority (highest first):**
  1. `SEARCHMUSE_LLM_API_KEY` (universal env var, wins for all providers).
  2. Provider-specific env var (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GOOGLE_API_KEY`).
  3. System keyring (via `keyring_store.get_api_key(provider)`).
  4. `llm.api_key` field in the YAML config.
- **Returns `None`** when none of the above yields a value — acceptable for Ollama which requires no auth.

## Environment Configuration

**Required (default Ollama provider):** none — base URL has a working localhost default.

**Conditionally required:**
- One of `SEARCHMUSE_LLM_API_KEY`, `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GOOGLE_API_KEY` (or a keyring entry) when `llm.provider != "ollama"`.

**Operational env vars (`.env.example`):** `SEARCHMUSE_LLM_BASE_URL`, `SEARCHMUSE_LLM_MODEL`, `SEARCHMUSE_MAX_ITERATIONS`, `SEARCHMUSE_MIN_SOURCES`, `SEARCHMUSE_REQUEST_DELAY`, `SEARCHMUSE_REQUEST_TIMEOUT`, `SEARCHMUSE_DB_PATH`, `SEARCHMUSE_LOG_LEVEL`. The generic `SEARCHMUSE_<SECTION>_<KEY>` mapping is documented in `src/searchmuse/infrastructure/config.py` header.

**Secrets location:** OS keyring (preferred) or environment variables / `.env` file (gitignored). `.env.example` ships only non-secret defaults; it contains no API keys.

## Webhooks & Callbacks

- **Incoming:** None. CLI-only application; no HTTP server.
- **Outgoing:** None. All external traffic is request/response (LLM APIs, DDG, scraped URLs, Ollama REST).

## Observability

- **Logging:** Standard `logging` module, configured by `src/searchmuse/infrastructure/logging_setup.py`. Level + optional file + timestamps come from `logging.*` config section. UI language switch (`logging.ui_language`) drives i18n via `src/searchmuse/infrastructure/i18n.py`.
- **Error tracking:** No external service — every adapter wraps third-party exceptions into domain errors (`src/searchmuse/domain/errors.py`) so the application layer handles a stable taxonomy.

---

*Integration audit: 2026-05-18*
