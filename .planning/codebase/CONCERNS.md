# Codebase Concerns

**Analysis Date:** 2026-05-18
**Project status:** `Development Status :: 2 - Pre-Alpha` (`pyproject.toml:17`). All concerns
below should be read with that pre-alpha context — no API stability or backwards-compat
guarantee exists yet (`docs/001_functional/010_roadmap.md:480-485`).

---

## 1. TODO / FIXME / XXX / HACK Markers

A recursive `grep -rn "TODO\|FIXME\|HACK\|XXX"` across both `src/searchmuse/` and `tests/`
returned **zero matches**. The only `placeholder` references in production code are benign
identifiers, not deferred-work markers:

- `src/searchmuse/adapters/llm/prompts.py:3` — docstring noting `{placeholders}` for
  `.format()` substitution.
- `src/searchmuse/adapters/repositories/sqlite_chat_repository.py:285-286` — local variable
  `placeholder_messages` used to satisfy a frozen-tuple constructor when only session
  metadata is being listed.

This is a positive signal but also means **debt is undocumented inline**; the canonical
debt list is the roadmap table (see §2) rather than code comments.

---

## 2. Known Limitations (Authoritative Self-Assessment)

These items are taken verbatim from the project's own functional docs and are the most
load-bearing source of truth for "what does not yet work".

### From `docs/001_functional/009_limitations.md`

**Scope (by design):**
- Not real-time — multi-minute latency due to scraping + LLM (`009_limitations.md:7-24`).
- No login/paywall content (`009_limitations.md:27-43`).
- No meaningful multimedia (image/video/audio) extraction
  (`009_limitations.md:47-69`).
- Not a structured-database query system (`009_limitations.md:72-86`).

**Quality (run-time risk):**
- Output quality is bounded by the chosen LLM; hallucinated numbers, outdated facts and
  bias are explicitly acknowledged (`009_limitations.md:92-117`).
- Extraction failure rates documented per site type — as low as 60 % for "custom layouts"
  (`009_limitations.md:165-187`).

**Technical (operational risk):**
- Hard dependency on robots.txt compliance (`009_limitations.md:193-208`).
- Self-imposed per-domain delays of 1–10 s — searches typically take 2–5 min
  (`009_limitations.md:212-225`).
- JS-heavy sites slow searches to 3–5 min via Playwright (`009_limitations.md:228-241`).
- Memory ceiling around 100 sources before issues (`009_limitations.md:245-263`).

**Known bugs explicitly enumerated (`009_limitations.md:446-466`):**
- Non-ASCII author names sometimes lost.
- Date parsing inconsistent across locales.
- Tables/code blocks lose formatting on extraction.
- LLM streaming sometimes drops tokens; temperature settings don't always apply.
- Very long content truncated in prompts.
- Queries `<3` chars rejected; non-Latin scripts sometimes fail.

### From `docs/001_functional/010_roadmap.md`

The roadmap exposes its own "Known Technical Debt" table (`010_roadmap.md:416-428`):

| Item | Severity | Target Version |
|------|----------|----------------|
| Improve error handling | High | v1.0 |
| Add comprehensive logging | High | v1.0 |
| Optimize memory usage | Medium | v1.0 |
| Refactor LLM adapters | Medium | v1.0 |
| Add async/await throughout | Low | v1.1 |
| Type hints coverage | Low | v1.0 |

Note that `010_roadmap.md` still lists 0.1.0 as "In Development" targeting Q2 2024 while
the current date is 2026-05-18 — **the roadmap dates are stale** and should not be used
to gauge progress.

---

## 3. Test Coverage Gaps

Coverage threshold is hard-enforced at 80 % (`pyproject.toml:151` →
`fail_under = 80`), but several `src/searchmuse/**` modules have **no matching
`test_*.py` file** under `tests/unit/`.

**Production modules with no dedicated unit-test file:**

| Source module | Path |
|---------------|------|
| `prompts.py` | `src/searchmuse/adapters/llm/prompts.py` |
| `errors.py` | `src/searchmuse/domain/errors.py` |
| `chat_repository_port.py` | `src/searchmuse/ports/chat_repository_port.py` |
| `content_extractor_port.py` | `src/searchmuse/ports/content_extractor_port.py` |
| `llm_port.py` | `src/searchmuse/ports/llm_port.py` |
| `result_renderer_port.py` | `src/searchmuse/ports/result_renderer_port.py` |
| `scraper_port.py` | `src/searchmuse/ports/scraper_port.py` |
| `search_port.py` | `src/searchmuse/ports/search_port.py` |
| `source_repository_port.py` | `src/searchmuse/ports/source_repository_port.py` |

**Assessment:**
- The `ports/*.py` are `typing.Protocol` definitions — direct unit tests add little value;
  they are exercised indirectly through adapter tests (e.g. `tests/unit/adapters/test_httpx_scraper.py`
  exercises `ScraperPort`). Acceptable gap.
- `domain/errors.py` (custom exception hierarchy, 111 lines, `src/searchmuse/domain/errors.py:1-111`)
  has no dedicated tests for the constructors / `.url` attribute attachment used by
  `httpx_scraper.py:239-242` and `playwright_scraper.py:108-114`. Worth a small test file.
- `adapters/llm/prompts.py` (117 lines of `{placeholder}` templates,
  `src/searchmuse/adapters/llm/prompts.py:1-117`) is reachable only via `_base.py`, but the
  JSON-shape contract embedded in `STRATEGY_PROMPT` (`prompts.py:41-46`), `RELEVANCE_PROMPT`
  (`prompts.py:69-72`) and `COVERAGE_PROMPT` (`prompts.py:90-94`) is fragile and would
  benefit from at least a "template renders with all required placeholders" snapshot test.
- `infrastructure/i18n.py` (508 lines, `src/searchmuse/infrastructure/i18n.py`) is the
  largest non-CLI module; `tests/unit/infrastructure/test_i18n.py` exists but, given its
  size, coverage of the long key tables is worth auditing.

There are **no `tests/integration/`** or `tests/e2e/` directories — only `tests/unit/`
exists, despite the user-rules baseline asking for all three layers
(`tests/` lists no integration or e2e subdirectories).

---

## 4. Security and Scraping Concerns

### 4.1 robots.txt — silent-permissive failure mode

`src/searchmuse/adapters/scrapers/httpx_scraper.py:262-277` fetches robots.txt and, on any
exception (`except Exception`), logs at WARNING and **caches a permissive empty parser** —
meaning a transient robots.txt fetch failure (timeout, 5xx) permanently un-blocks the
domain for the lifetime of the adapter instance. The `_ROBOTS_TXT_TIMEOUT` is 5 s
(`httpx_scraper.py:49`) and there is no retry. Calling adapter `close()` resets the cache,
but the behaviour should at minimum be documented as "fail-open".

### 4.2 robots.txt — not enforced in Playwright path

`src/searchmuse/adapters/scrapers/playwright_scraper.py` performs rate limiting
(`playwright_scraper.py:168-182`) but contains **no robots.txt check** equivalent to
`httpx_scraper.py:108-109`. When `config.scraping.use_playwright` is true
(`config/default.yaml:49`) the `respect_robots_txt: true` setting (`config/default.yaml:45`)
is effectively ignored.

### 4.3 Per-domain rate limiting — not cross-adapter

Each adapter instance keeps its own `self._last_request_times` dict
(`httpx_scraper.py:75`, `playwright_scraper.py:48`). When both adapters run against the
same domain (e.g. fallback strategy), the configured `request_delay`
(`config/default.yaml:39`, default 1.0 s) is enforced **per adapter** rather than
per-domain globally. Bot-detection back-off therefore halves.

### 4.4 Prompt-injection surface from scraped content

The relevance and coverage prompts inline scraped page text directly:
- `src/searchmuse/adapters/llm/prompts.py:53-72` (`RELEVANCE_PROMPT`) interpolates
  `{title}`, `{url}` and `{content_text}` from arbitrary remote HTML.
- `src/searchmuse/adapters/llm/prompts.py:79-94` (`COVERAGE_PROMPT`) interpolates
  `{source_summaries}` built from the same untrusted content.
- `src/searchmuse/adapters/llm/prompts.py:101-117` (`SYNTHESIS_PROMPT`) interpolates the
  full `{source_details}` and instructs the model to obey citation rules — a hostile page
  can instruct the model to ignore those rules.

`docs/002_technical/009_security.md:156-187` claims SearchMuse "protects against prompt
injection" via input validation and "Sanitization of special characters", but **no
sanitization step is applied to scraped content** before it reaches the prompts:
`src/searchmuse/application/search_orchestrator.py:221-262` passes
`content.clean_text` straight through to `self._llm.assess_content_relevance(...)` with no
escaping or wrapper guard. The docs also describe `llm.verify_responses` /
`validation_rules` config keys (`009_security.md:208-218`) which **do not exist** in
`config/default.yaml` or `src/searchmuse/infrastructure/config.py:35-46`. The docs are
aspirational, not current.

### 4.5 Optional-provider API key handling

`src/searchmuse/infrastructure/api_key_resolver.py:28-59` resolves API keys in the
documented priority order: `SEARCHMUSE_LLM_API_KEY` → provider-specific env vars
(`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GOOGLE_API_KEY`) → keyring → YAML config.

**Concerns:**
- The YAML config field `llm.api_key` (`config/default.yaml:11`, `config.py:46`) accepts a
  plaintext key. There is no validation forbidding it; users who commit a non-default
  config file may leak secrets. `docs/002_technical/009_security.md:336-352` warns
  against this but provides no enforcement.
- `src/searchmuse/infrastructure/keyring_store.py:19-25` makes `keyring` an optional
  import that **silently degrades to "no keyring available"** when missing
  (`keyring_store.py:33-35`). When the user thinks their key is in the keyring but the
  optional extra was not installed, resolution silently falls through to the YAML field
  (`api_key_resolver.py:51-57`). No warning is logged.
- `keyring_store.py:46-51` swallows all exceptions from `_keyring.get_password(...)` with
  a DEBUG-level log only — a broken keyring backend (D-Bus, Keychain locked) is
  indistinguishable from "no key stored".

### 4.6 Misleading default User-Agent

`config/default.yaml:47` sets:
`SearchMuse/0.1.0 (research-assistant; +https://github.com/user/searchmuse)` — the
`github.com/user/...` URL is a **placeholder that does not resolve**, while the real repo
is `https://github.com/fedcal/SearchMuse` (per `pyproject.toml:73-76`). Site operators
receiving abuse complaints cannot reach the maintainer. Compare with the (also stale)
example in `docs/002_technical/009_security.md:127-130`
(`+https://github.com/yourorg/searchmuse`).

---

## 5. Dependency Risks

Source: `pyproject.toml:30-67`.

### Pre-1.0 runtime dependencies

| Package | Pin | Risk |
|---------|-----|------|
| `ollama>=0.4` | `pyproject.toml:36` | 0.x SDK; breaking changes likely. |
| `duckduckgo-search>=8.0` | `pyproject.toml:41` | Repeatedly renamed/forked; project README on PyPI now redirects users to the `ddgs` package. The project context flags `ddgs` as a concern even though the install is still via `duckduckgo-search`. Wrapped in `src/searchmuse/adapters/scrapers/duckduckgo_search.py:15` (`from duckduckgo_search import DDGS`) — a single import that will need migration. |
| `readability-lxml>=0.8` | `pyproject.toml:34` | Long-unstable upstream; alternate path via trafilatura already present. |
| `aiosqlite>=0.20` | `pyproject.toml:40` | 0.x. |

### Pre-1.0 optional providers

`pyproject.toml:45-48`: `anthropic>=0.39`, `openai>=1.50`, `google-genai>=1.0`,
`keyring>=25.0`. The LLM provider SDKs are all on a fast-moving release cadence and the
adapters (`src/searchmuse/adapters/llm/{claude,openai,gemini}_adapter.py`) are thin
wrappers — any SDK breaking change will surface immediately in the tests.

### Heavyweight required dep

`playwright>=1.45` (`pyproject.toml:32`) is a **required** runtime dependency, not
optional. The Python wheel pulls in browser binaries via `playwright install`, which:
- Adds ~300 MB to a fresh install (Chromium).
- Requires a separate install step (`playwright install chromium`) not handled by
  `pip install` alone.
- Means CI matrix in `.github/workflows/ci.yml:30-41` does NOT run browser binaries
  installation, so `tests/unit/adapters/test_playwright_scraper.py` must rely entirely on
  mocks. A regression in the real browser interaction would not be caught by CI.

Recommendation: move `playwright` to an optional extra (`searchmuse[playwright]`) gated by
`config.scraping.use_playwright = true` (`config/default.yaml:49`, default `false`).

### HTTP/2 via httpx

`httpx[http2]>=0.27` (`pyproject.toml:31`) brings in `h2` and `hpack` transitively. The
scraper enables HTTP/2 unconditionally (`src/searchmuse/adapters/scrapers/httpx_scraper.py:184-189`,
`http2=True`). Some servers behave differently on h2 vs h1.1 (notably around connection
re-use and rate limiting); when troubleshooting per-domain blocking, h2 should be
considered a variable.

### No dependency pinning / no lockfile

`pyproject.toml` uses `>=` pins exclusively. There is no `requirements.txt`,
`uv.lock`, or `poetry.lock` in the repo root. The security doc
(`docs/002_technical/009_security.md:318-332`) explicitly recommends pinning, but the
recommendation is not followed.

---

## 6. CI / Repo Hygiene

### CI workflows (`.github/workflows/`)

- `.github/workflows/ci.yml:30-41` runs the test matrix on Python 3.11/3.12/3.13 but does
  **not** install Playwright browser binaries — see §5.
- `.github/workflows/ci.yml:18` runs `ruff check src/ tests/` but **never runs `ruff
  format --check`**; formatting drift will not fail CI.
- `.github/workflows/ci.yml:20-28` runs `mypy src/searchmuse/` in strict mode
  (`pyproject.toml:111-122`), but only on Python 3.12 — typing regressions specific to
  3.11 or 3.13 are not caught.
- No coverage upload step despite `--cov` being passed
  (`.github/workflows/ci.yml:41`); the `fail_under = 80` gate (`pyproject.toml:151`) is
  enforced locally only.
- No `pip-audit` / `safety` / Dependabot job, even though
  `docs/002_technical/009_security.md:285-302` recommends them.

### Docs workflows

- `.github/workflows/docs.yml` and `.github/workflows/docs-check.yml` both run
  `mkdocs build --strict` (`docs.yml:45`, `docs-check.yml:36`). The recent commit
  `9a1f560 fix(docs): remove broken links causing mkdocs strict build failure` confirms
  the strict build has been brittle in practice.

### `site/` directory

`.gitignore:64-65` ignores `/site/` but the directory **is currently present in the
working tree** (`/media/federicocalo/D1/prj/WebScraping/site/`) with `index.html`,
`assets/`, `sitemap.xml`, etc. The git history shows it was tracked in commit
`7cb64be docs: publish project documentation via GitHub Pages` and is now untracked.
The local directory is stale build output that can confuse contributors; it should be
removed locally (`rm -rf site/`) since `.github/workflows/docs.yml:50` re-builds it on
every deploy.

### `.coverage` artifact tracked-in-tree

`/media/federicocalo/D1/prj/WebScraping/.coverage` (131 KB, last modified Feb 28) is
present in the working tree. `.gitignore:29` excludes it from commits but the file is
still on disk and may be loaded by `pytest-cov` runs as combined data.

### Placeholder URLs still in repo

- `config/default.yaml:47` — `https://github.com/user/searchmuse` (see §4.6).
- `docs/002_technical/009_security.md:129` — `https://github.com/yourorg/searchmuse`.
- `docs/002_technical/009_security.md:460,483` — vulnerability reporting address
  `security@example.com`, contradicting `SECURITY.md:17` which gives the real address
  `fedcal01@gmail.com`. Two security contacts is a documentation defect.

### Branch naming inconsistency

Workflows already reference `master` (`.github/workflows/ci.yml:5-7`) after the fix in
commit `8049de5`. No lingering `main` references in workflows. ✓

---

## 7. Fragile Areas

### `src/searchmuse/adapters/llm/prompts.py` (entire file)

The three structured prompts (`STRATEGY_PROMPT` lines 24-46, `RELEVANCE_PROMPT` lines
53-72, `COVERAGE_PROMPT` lines 79-94) instruct the LLM to "Respond with ONLY a valid JSON
object — no markdown fences, no extra text". Any wording drift here will break the
downstream parsers in `src/searchmuse/adapters/llm/_helpers.py` and the coverage
extraction in `src/searchmuse/application/search_orchestrator.py:344-350`
(`_parse_coverage_score`, which does `float(assessment.split("|", 1)[0])`). Small prompt
tweaks → silent failure → fallback coverage score → premature exit.

### `src/searchmuse/application/search_orchestrator.py:281`

Coverage state is packed into a single string:
`coverage_assessment=f"{coverage_score:.2f}|{coverage_text}"`. The pipe character is the
implicit schema; if either side ever contains `|` the parser at
`search_orchestrator.py:344-350` silently breaks (`ValueError` is caught and falls
through). A proper dataclass field on `SearchIteration` would be more robust.

### `src/searchmuse/application/search_orchestrator.py:221-228`

`extract()` failures are swallowed at DEBUG level (`logger.debug("Extraction failed for
%s", page.url)`) with no propagation. Same pattern at lines 240-246 for relevance
assessment. With LOG_LEVEL=INFO (the documented default in `.env.example`) the operator
gets no visibility into systematic extraction failures.

### `src/searchmuse/adapters/scrapers/httpx_scraper.py:298-299`

`raw_body = response.text[: self._config.max_page_size]` truncates **after** the entire
body has been read into memory — `max_page_size` (5 MB default, `config/default.yaml:51`)
does not protect against a malicious server streaming a 1 GB body. Switch to streaming
reads with `response.iter_bytes()` + early abort.

### `src/searchmuse/infrastructure/i18n.py` (508 lines)

Largest non-CLI module. Translation keys are referenced from many call sites
(`grep "t(" src/searchmuse/` yields dozens). Renaming or removing a key is a silent
runtime breakage. The module merits a "all referenced keys exist in all languages" lint.

### `src/searchmuse/cli/interactive.py` (625 lines)

Largest module in the codebase. Mixes REPL loop, command dispatch, chat persistence and
error rendering. Touching one concern (e.g. adding a new slash command) risks regressing
others. Refactor candidate per the user-rules guideline of `200-400 lines typical, 800
max`.

### `src/searchmuse/adapters/repositories/sqlite_repository.py` (393 lines) and `sqlite_chat_repository.py` (335 lines)

Two repositories share a SQLite file but maintain their own schemas. Migration story is
unclear — there is no `alembic`/`yoyo`/`sqlite-utils` migration framework in
`pyproject.toml:30-42`. Schema changes will silently break existing user databases at
`~/.searchmuse/searchmuse.db` (`config/default.yaml:65`).

### `src/searchmuse/adapters/scrapers/httpx_scraper.py:215` and `playwright_scraper.py:179-182`

Per-domain rate-limit state is updated via `{**self._last_request_times, domain: ...}` —
this respects the project's immutability rule but allocates a new dict on every request.
Acceptable now; will become a hot-spot with high domain cardinality.

---

*Concerns audit: 2026-05-18*
