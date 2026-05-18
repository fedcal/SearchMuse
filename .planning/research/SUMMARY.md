# Project Research Summary

**Project:** SearchMuse v0.2 — Perplexity-like CLI Foundation
**Domain:** Local-first, CLI-first, Perplexity-like answer engine (Python, hexagonal, brownfield pre-alpha)
**Researched:** 2026-05-18
**Confidence:** HIGH

> Synthesis of four parallel research outputs (STACK, FEATURES, ARCHITECTURE, PITFALLS) for the v0.2 milestone. This file is the canonical context for requirements definition and roadmap creation — downstream agents should consult this instead of the full 1872 lines.

---

## Executive Summary

SearchMuse v0.2 is a **brownfield hardening + extension milestone** on an already-working hexagonal Python CLI: streaming synthesis, inline rich citations, Quick + Pro Search split, multi-turn session persistence, one Focus Mode, and a `history` command. The architecture is sound and stays put — every new capability flows through the existing `domain → ports ← adapters` triangle with the `application/` layer as the use-case host. No new paradigms, no new language, no web/API surface.

The three biggest strategic calls — independently surfaced by **three** of the four researchers — are: **(1) Focus Mode v1 = Academic** (the only choice that meaningfully validates the Focus pattern and exploits the local-first privacy wedge that researchers actually need), **(2) the `duckduckgo-search` → `ddgs` migration is non-negotiable and goes in Phase 1** (upstream package is end-of-life, single point of failure for the entire product), and **(3) the LLM port grows a sibling `stream_synthesize_answer` method rather than replacing `synthesize_answer`** — preserving backward compatibility and matching the dominant Python LLM-SDK idiom (OpenAI, Anthropic, Ollama, LlamaIndex, LangChain all do dual-method).

The dominant risk profile is **silent correctness regressions**, not feature complexity: prompt injection through scraped HTML, hallucinated citations on the default 7-8B Ollama model, infinite Pro Search loops biased by a brittle `score|text` parser that silently falls back to `0.0`, SQLite schema drift breaking user history when migrations aren't in place, and the existing `searchmuse search …` CLI surface accidentally changing. Mitigation is **front-loaded into Phase 1 (Platform Hardening)** before any new feature ships, then enforced by three test layers (unit / integration-with-cassettes / opt-in eval-against-real-Ollama) introduced alongside streaming in Phase 2.

---

## Key Findings

### Recommended Stack

The existing core stack (`httpx`, `trafilatura`, `readability-lxml`, `typer`, `rich`, `aiosqlite`, `ollama`, `pytest`, `mypy strict`, `ruff`) is **kept verbatim**. The v0.2 delta is small: bump LLM SDK minimums for native streaming, replace one search lib, add structured-output + academic-source libs.

**Core delta (full table in `STACK.md`):**

- **`ddgs >= 9.14.4`** replaces `duckduckgo-search` — same upstream maintainer, the old name is end-of-life; new package is a metasearch aggregator with automatic failover (DDG → Bing → Brave). Single-line import change, single-line `pyproject.toml` change.
- **`instructor >= 1.15.1`** — one library, four LLM providers, gives us validated Pydantic-modelled structured outputs (kills the fragile `_parse_coverage_score` regex; unblocks Pro Search v2 visible stop-criteria).
- **`pydantic >= 2.8`** as a direct dep — first Pydantic in `domain/` (only for the `CoverageAssessment` schema contract).
- **`pyalex >= 0.21`** behind an optional `[academic]` extra — OpenAlex client for Academic Focus Mode (free API key now mandatory since 2026-02-13).
- **Bump:** `ollama >= 0.6.2`, `openai >= 1.55`, `anthropic >= 0.40`, `google-genai >= 1.10`, `rich >= 13.7`.
- **Remove:** `duckduckgo-search`.
- **Optional extras:** `[academic]` (pyalex), `[brave]` (key-only, no SDK), `[all-providers]`.

**Streaming pattern (Rich):** `Live(Markdown(...), refresh_per_second=4-8)` with a `safe_tail` buffer that auto-closes dangling `**` / `` ` `` / `[` for render-only — raw buffer stays unchanged. Hard rule: one `Live` per `Console`, no nested `Progress`.

**Persistence:** stay on `aiosqlite`. SQLModel / SQLAlchemy / sqlite-utils all rejected (ORM bloat for a 3-table single-user local DB; `sqlite-utils` is sync-only and would strictly regress). Migrations via `PRAGMA user_version` + numbered `.sql` files (~30 LOC runner, no Alembic).

### Expected Features

Mapped 1:1 to PROJECT.md Active requirements plus research-identified non-negotiables. Full landscape, prioritization matrix, and competitor comparison in `FEATURES.md`.

**Must have (P1 — required for v0.2 launch):**

- Streaming token-by-token synthesis (Ollama / Claude / OpenAI / Gemini, all already streamable)
- Inline `[N]` citations + OSC 8 clickable links + Rich sources panel (one cohesive workstream, not three)
- Quick Answer mode (`--quick`, single round, 1-2 sources, < 5s first-token target on local 7-8B)
- Pro Search v2 with **explicit visible stop criteria** + per-iteration progress events
- Multi-turn session persistence — auto-create, auto-save (including citations), rule-based auto-title
- **Focus Mode v1 = Academic** (see convergence below)
- `searchmuse history` command — `list` / `show` / `delete` / `rename` / `resume`
- EN + IT MkDocs documentation of new UX
- **Privacy receipt** footer (low cost, doubles as on-brand trust signal)

**Should have (P1–P2 — high value, low marginal cost on top of P1):**

- Evidence-chain inspector (`/explain`) — surfaces per-iteration searches, sources, scores, gap analysis, stop reason. The differentiator that makes "verifiability" tangible. Slip to v0.2.1 acceptable.
- Content-hash + excerpt on every Citation → enables `history verify <id>` ("source changed since cited")
- Auto-routing Quick vs Pro classifier (heuristic baseline)

**Defer (P3 — v0.3+):**

- Second Focus Mode (only after Academic pattern validated)
- Reproducibility (`--snapshot` / `--replay`) — high value, narrow audience; v0.3
- Web UI / HTTP API / Deep Research mode — separate milestones (already Out of Scope per PROJECT.md)
- SQLite FTS5 search across history, follow-up question generation, trace mode (`--trace`), local-document RAG — all v0.3+
- Auto-fact-checking, PDF export, browser extensions, multi-user — anti-features or v0.4+

### Architecture Approach

Strict hexagonal, brownfield-additive. Full design with diagrams in `ARCHITECTURE.md`.

**Key architectural calls (all three independent research streams converged):**

1. **LLM port dual-method, not replacement.** Add `LLMPort.stream_synthesize_answer(...) -> AsyncIterator[LLMChunk]` next to existing `synthesize_answer(...) -> str`. Default fallback in `BaseLLMAdapter` yields the batch result as one terminal chunk. Only `synthesize_answer` streams; strategy/relevance/coverage stay batch (short structured outputs).

2. **Reuse `ChatSession` / `ChatMessage` — do NOT introduce a parallel `Session` entity.** Extend the existing frozen dataclasses with `citations: tuple[Citation, ...]`, `focus_mode`, `model_used`, `search_result_id`. Schema evolution is **additive only** (`ALTER ADD COLUMN` + one `message_citations` child table for unbounded citation count), gated by `PRAGMA user_version` migration runner shared across `SqliteRepository` and `SqliteChatRepository`.

3. **Focus Mode = first-class domain value object + small application-layer registry**, not a Strategy class hierarchy and not a new port. `FocusMode` bundles `search_adapter_key`, `prompt_pack`, `scraping_overrides`, `citation_style`, `source_filters`. Container resolves `search_adapter_key` against an adapter registry at composition time; the orchestrator stays oblivious.

4. **Quick vs Pro = `SearchStrategyPort` Protocol with two implementations** (`QuickAnswerStrategy`, `IterativeSearchStrategy`). Today's `SearchOrchestrator` shrinks to a ~30-line dispatcher; the iterative loop is a lift-and-shift refactor (must be byte-for-byte equivalent — snapshot test).

5. **CLI ↔ application streaming boundary = `AsyncIterator[StrategyEvent]`** where `StrategyEvent = ProgressEvent | TokenEvent | CitationDiscoveredEvent | SearchResultEvent`. CLI consumes via `async for event: match event`. No event bus, no `asyncio.Queue` in the public API. Existing sync `ProgressCallback` stays for `searchmuse search`; interactive REPL uses the new iterator.

6. **Stop criteria as a domain value object** (`StopCriteria` frozen dataclass with `should_stop(state, elapsed) -> (bool, reason)`). Pulls four scattered conditions into one testable place and gives the CLI the reason string for "ispezione della catena di evidenza".

**Component map (NEW vs TOUCHED):**

- **NEW:** `application/quick_answer.py`, `application/iterative_search.py`, `application/focus_modes.py`, `application/events.py`, `domain/focus_mode.py`, `domain/stop_criteria.py`, `cli/history_commands.py`, eval + cassette test infra
- **TOUCHED (additive):** `domain/models.py` (chat field additions, `LLMChunk`), `ports/llm_port.py` (stream method), `ports/chat_repository_port.py` (3 new query methods), `application/search_orchestrator.py` (slimmed), `adapters/llm/_base.py` + each provider (streaming impl), `adapters/repositories/sqlite_chat_repository.py` (migration + queries), `cli/container.py` (registries), `cli/interactive.py` (streaming consumer)
- **UNCHANGED:** scrapers, extractors, `json_renderer.py`, `plain_renderer.py`, `infrastructure/*` (mostly), `domain/errors.py`, `domain/validators.py`

### Critical Pitfalls

Top 5 (full 12 in `PITFALLS.md`, plus tech-debt / integration / performance / security / UX tables).

1. **`ddgs` migration is a Phase-1 prerequisite, not a future tidy-up.** `duckduckgo-search` is end-of-life upstream; one library, one adapter, zero fallback = whole product dies on the next DDG HTML change. **Prevent:** swap import to `ddgs`, ship at minimum a stub second `SearchPort` adapter (SearXNG recommended — Docker one-liner for the user, ~50 LOC adapter), add an opt-in `@pytest.mark.live` canary that runs once a day asserting "DDG returns ≥1 result for `python`".

2. **Prompt injection via scraped page content.** `RELEVANCE_PROMPT` and `SYNTHESIS_PROMPT` interpolate `{content_text}` / `{source_details}` raw. `009_security.md` claims defenses (`llm.verify_responses`, `validation_rules`) that **do not exist in code** — this is documentation fraud and must be rewritten or implemented. **Prevent:** structural fencing with a per-request random nonce in the delimiter, strip invisible Unicode + obvious "ignore previous" markers, schema-strict JSON for assessment (reject malformed instead of silently falling back), reject any URL in synthesis output that wasn't in the input source set.

3. **Hallucinated citations — `[3]` cites URL that doesn't support the claim.** Endemic to RAG, worst on the 7-8B local default. **Prevent:** give the LLM only `[1]…[N]` markers + a separate mapping (forbid raw URLs in body); post-hoc substring/fuzzy match on noun phrases between the cited source's text and the surrounding sentence; flag unsupported brackets visually (`[3⚠]`); restrict Quick Answer to lower temperature + stricter "if sources don't cover the question, say so" prompt. Build an eval fixture set (10-20 Q/A/expected-source triples) and run weekly, not per-commit.

4. **Infinite Pro Search loop biased by silent parser fallback.** Existing `_parse_coverage_score` silently returns `0.0` on malformed output → loop thinks "not enough info, iterate more" → runs forever, especially with local models. **Prevent:** kill the `score|text` packed string in favour of a Pydantic-validated `CoverageAssessment` (this is exactly why `instructor` is in the stack); add **five stop criteria** (`max_iterations`, `min_coverage_score` for N consecutive iterations, wall-clock budget, token budget for cloud, no-progress detector ≥ X% delta); Quick Answer is hard-capped to 1 iteration; `Ctrl+C` flushes the partial session marked `interrupted`, never corrupts the DB.

5. **SQLite schema migrations without a framework break user databases.** Adding a column to `chat_messages` quietly works on fresh DBs, quietly breaks on old DBs with `OperationalError: no such column` — at exactly the moment users start caring about their `history`. **Prevent:** `PRAGMA user_version` runner committed in the same phase as session persistence, numbered `migrations/000N_*.sql` files, forward-only, shared across both repositories, `.bak-YYYYMMDD` on first migration, integration test that fixture-loads a v0.1 DB and asserts no data loss.

Two more that didn't make the top-5 cut but are still phase-blocking:

- **Streaming Markdown flicker / broken intermediate parses** — partial code fences render as garbage. Buffer first, render at natural boundaries (newline, sentence, complete fence), cap `refresh_per_second` to 4-8, detect unclosed fences and visually close them for render only. Verify the streaming path degrades cleanly to line-buffered plain text when piped to `less`.
- **`searchmuse search …` CLI surface accidentally breaks.** PROJECT.md hard constraint. **Prevent:** CLI surface snapshot test in CI (`typer.testing.CliRunner` against `--help` for every command/subcommand) landed in Phase 1 so every subsequent PR sees the guard. New commands are additive top-level (`searchmuse history`, never `searchmuse query search`).

---

## Implications for Roadmap

Six suggested phases. All four research streams converged on the **same build order** with minor variations; the version below is the consensus. Each phase is independently shippable, leaves the codebase green (mypy strict + ruff + ≥ 80% coverage), and fits the ~5h/week + 1-3 calendar week constraint.

### Phase 1: Platform Hardening + Domain Extensions

**Rationale:** Three of four research streams flagged the same Phase-1 must-dos before any new feature ships. Pitfalls 3, 8, 12 plus the prompt-injection fixture and CLI snapshot test are non-feature work that every subsequent phase depends on — skipping pays compound interest. Adding pure domain types (`FocusMode`, `StopCriteria`, `LLMChunk`, `CitationStyle`, event union, chat field additions) up front means later phases just `import` and don't refactor.

**Delivers:**
- `ddgs` migration (single-line import + `pyproject.toml` rename) + minimum one fallback `SearchPort` adapter (SearXNG recommended)
- Politeness fix-up: real User-Agent URL, cross-adapter shared rate limit, robots.txt **fail-closed** on fetch failure, robots.txt enforced on the Playwright path too
- CLI surface snapshot test (`tests/unit/cli/test_cli_surface.py`)
- New domain types (frozen dataclasses, zero behaviour change): `FocusMode`, `StopCriteria`, `LLMChunk`, `CitationStyle`, `TokenEvent`, `CitationDiscoveredEvent`, `SearchResultEvent`
- Aspirational `009_security.md` claims removed or implemented (no middle ground)
- `pyproject.toml` cleanup: optional `[academic]` / `[brave]` / `[all-providers]` extras; Playwright moved to extra; `pip-audit` job added to CI

**Addresses (FEATURES.md):** none directly — pure debt + foundation
**Avoids (PITFALLS.md):** 3, 8, 12 (foundational); enables 1, 2, 7, 11 to be fixable in later phases

### Phase 2: Streaming + Quick Answer + Test Infrastructure

**Rationale:** Streaming is on the critical path for every other UX-visible feature (Pro Search progress, evidence-chain, perceived liveness). Quick Answer rides the same wave — single search round + streaming synthesis is the smallest end-to-end vertical slice of the new architecture. Cassette + eval test infra ships here because streaming itself needs replayable fixtures, so the two pay for each other. Prompt-injection fencing lands here because Phase 2 is the first phase that meaningfully touches `prompts.py`.

**Delivers:**
- `LLMPort.stream_synthesize_answer` + `BaseLLMAdapter` fallback + native impl in Ollama adapter (others get fallback initially)
- Rich `Live` + `safe_tail` streaming display with plain-text fallback for non-TTY / piped invocations
- `SearchStrategyPort` Protocol + `QuickAnswerStrategy` + `IterativeSearchStrategy` (latter is **pure refactor**, byte-for-byte parity required, snapshot-tested)
- `SearchOrchestrator` slimmed to dispatcher
- `searchmuse search --quick` / `--pro` CLI flags (default stays `pro` to preserve back-compat)
- Three test layers established: `tests/unit/` (mocks, fast), `tests/integration/` (LLM cassettes), `tests/eval/` (real Ollama Mistral, opt-in `make eval`, baseline-vs-regression)
- Prompt injection fencing (structural delimiters + nonce + marker stripping)

**Uses (STACK.md):** `ollama >= 0.6.2` streaming, Rich `Live` + `Markdown`
**Implements (ARCHITECTURE.md):** dual-method LLM port, `AsyncIterator[StrategyEvent]` boundary, strategy split
**Avoids (PITFALLS.md):** 1, 4, 6, 10

### Phase 3: Pro Search v2 + Citation Pipeline

**Rationale:** Pro Search v2 explicitly needs visible stop criteria — which requires `instructor` + the `CoverageAssessment` Pydantic model in the domain (killing the silent `0.0` fallback). The citation pipeline (numbered `[N]` → OSC 8 clickable → Rich sources panel → content hash + excerpt) is one cohesive workstream; FEATURES.md is explicit "do it as one phase, not three half-cuts". Pitfall 2 (hallucinated citations) verification logic lands here because this is the phase that owns the bracket → source mapping.

**Delivers:**
- `instructor` integration in every LLM adapter; `LLMPort.assess_coverage_structured` returning `CoverageAssessment`
- All five stop criteria implemented in `StopCriteria.should_stop` (max iters, min coverage for N consecutive, wall-clock, token budget, no-progress)
- Per-iteration `ProgressEvent` enrichment: "Iteration 2/5 — coverage 0.62 — searching: '…'"
- Surfaced stop reason in output: "Stopped after 3 iterations: coverage 0.78 ≥ 0.7, sources 11 ≥ 5"
- Inline `[N]` citations as Rich Markdown links → OSC 8 in supported terminals, graceful degradation elsewhere
- Rich sources panel (clickable URLs)
- Citation `content_hash: str` + `excerpt: str` (enables future `history verify`)
- Post-hoc bracket-to-source mechanical check; unsupported brackets flagged `[N⚠]`
- `Ctrl+C` cleanly flushes partial session with `interrupted` marker

**Uses (STACK.md):** `instructor`, `pydantic`, `rich >= 13.7` OSC 8
**Avoids (PITFALLS.md):** 2, 7

### Phase 4: Session Persistence + `history` Command + Migrations

**Rationale:** Sessions / history / resume / rename all depend on the same already-existing `ChatRepositoryPort` — bundle them, marginal cost of `rename` once `list` and `show` exist is hours. Schema migration runner is a **prerequisite for Focus Mode** (Phase 5 may add per-mode preferences) and must land before users accumulate data, hence here not later.

**Delivers:**
- `PRAGMA user_version` migration runner shared across `SqliteRepository` and `SqliteChatRepository`; numbered `migrations/000N_*.sql`; `.bak-YYYYMMDD` on first migration; integration test fixture-loading a v0.1 DB
- Additive schema: 5 new columns on `chat_sessions` / `chat_messages` + `message_citations` child table + 2 indexes
- End-to-end session wiring: auto-create on REPL start, auto-save every turn (with citations, focus mode, model used), rule-based auto-title from first query
- Three new `ChatRepositoryPort` methods: `search_messages`, `list_sessions_by_focus`, `load_session_with_citations`
- `searchmuse history list` (Rich table — paginated, indexed query, < 500ms at 100+ sessions)
- `searchmuse history show <id>` (replay, with `--explain` flag stub for Phase 5 evidence-chain)
- `searchmuse history delete <id>` / `rename <id> "name"` / `resume <id>`
- `searchmuse history --stats` (DB path + size + session count; warns > 500 MB)
- Tiered storage from day one: always-store metadata + answer + URLs + titles + relevance; opt-in `keep_extracted_text` (default ON for audit); opt-in `keep_raw_html` (default OFF)
- Retention policy: `storage.session_retention_days: 90` default; manual `searchmuse maintenance prune`
- `PRAGMA journal_mode=WAL` + `auto_vacuum=INCREMENTAL`

**Avoids (PITFALLS.md):** 5, 11

### Phase 5: Focus Mode v1 (Academic)

**Rationale:** Three of four research streams converged on **Academic** over Web. Reasons (in order of weight): (1) it's the *only* mode that meaningfully validates the Focus pattern — Web Focus is a near-no-op since today's default is already broad DDG; (2) it exploits the local-first privacy wedge that PROJECT.md's target users (researchers, journalists, analysts handling unpublished/sensitive work) literally cannot get from Perplexity Pro; (3) source-filter heuristic is well-defined and stable for academic (DOI / `*.edu` / known journal domains) — Web's filter is the unsolved hard problem of search; (4) opt-in only, cannot regress default behaviour. Comes after Phase 4 because Focus Mode may need per-session preferences (migration runner must already exist).

**Delivers:**
- `FocusMode` dataclass + `WEB_MODE` / `ACADEMIC_MODE` instances + `REGISTRY` in `application/focus_modes.py` + `apply_focus_overrides()` pure function
- New `OpenAlexSearchAdapter(SearchPort)` behind `[academic]` extra (`pyalex >= 0.21`, wrapped in `asyncio.to_thread`)
- `Container` resolves `focus_mode.search_adapter_key` against the adapter registry at composition time
- Per-mode prompt pack `adapters/llm/prompts/focus_academic.py` (strategy / relevance / synthesis overrides emphasising peer-review status, methodology, formal hedging)
- Source-filter with safe fallback: drop non-allowlist URLs unless iteration would return < 3 sources (fallback to web with warning, never zero-result)
- CLI: `searchmuse search --focus academic`; REPL `/focus academic` and `/focus web`; sticky per-session via `chat_sessions.default_focus_mode`
- Academic display: sources panel shows DOI / journal / year when extractable
- "Focus filtered N sources — try `--focus web`" warning when > X% of results filtered
- Eval fixture: ≥ 10 Q/A pairs proving Academic mode actually helps vs default
- Governance rule in `CONTRIBUTING.md`: new Focus modes require ≥ 10 user upvotes + eval fixture + maintainer commits to one year of green eval (caps mode proliferation)

**Uses (STACK.md):** `pyalex >= 0.21`, OpenAlex API key via existing `api_key_resolver.py` chain
**Avoids (PITFALLS.md):** 9

### Phase 6: Documentation (MkDocs EN + IT)

**Rationale:** Already a stated milestone deliverable. Shadows phases 2-5 with per-PR doc updates rather than a single late phase, but a final pass at the end consolidates the "Upgrading from 0.1 → 0.2" section, ensures EN/IT parity (small lint test), and runs `mkdocs build --strict` to catch broken links (PR `9a1f560` proved this is brittle).

**Delivers:**
- `docs/001_functional/` updated for streaming, Quick vs Pro, `history`, `--focus`, citation UX
- New `docs/00X_upgrading-0.1-to-0.2.md` listing every behaviour change with old → new examples
- EN + IT pages for `history`, `resume`, `--quick`, `--focus`, citation UX
- `tests/unit/infrastructure/test_i18n_completeness.py` (all keys exist in all langs)
- `mkdocs build --strict` in pre-commit or documented `make` target

### Phase Ordering Rationale

- **Phase 1 first** because Pitfalls 3, 8, 12 are cross-cutting product killers — every subsequent phase pays interest if these slip. Domain extensions are pure additions, zero behaviour change, and unblock parallel work in Phases 2/3/4/5.
- **Phase 2 before Phase 3** because Pro Search v2 (Phase 3) needs the streaming progress channel and the eval / cassette test infra to be confident the iterative refactor stays behaviour-equivalent.
- **Phase 3 before Phase 4** in calendar order, but they share no surface — could be parallelised by two contributors. Listed sequentially because the citation pipeline is on the critical path for Phase 4's session-with-citations storage shape.
- **Phase 4 before Phase 5** because the migration runner (Phase 4) is a hard prerequisite for any per-mode schema change (Phase 5).
- **Phase 5 last among features** because Focus Mode is opt-in by definition and cannot regress default behaviour; it benefits maximally from a hardened, streaming, citation-verified, session-persistent foundation.
- **Phase 6 is continuous + final pass** — docs writer shadows each PR; final pass consolidates and runs strict build.

Total: ~11-13 calendar weeks at 5h/week (matches ARCHITECTURE.md effort estimate and the "fasi piccole, indipendenti, 1-3 settimane" constraint).

### Research Flags

Phases likely needing **deeper research during planning** (`/gsd:plan-phase --research-phase N`):

- **Phase 2 (Streaming + Quick Answer):** the `safe_tail` Markdown auto-close heuristic is well-known but every reference impl handles edge cases differently (nested fences, dangling list markers). One spike to pick a concrete approach before coding.
- **Phase 3 (Pro Search v2 + Citations):** post-hoc citation verification has at least three viable approaches (substring match, fuzzy match, local NLI model). Trade-off between false-positive flag rate and Ollama inference cost needs empirical testing before committing.
- **Phase 5 (Focus Mode v1 — Academic):** OpenAlex API behaviour with the mandatory key + relevance-assessment LLM's behaviour on academic-language sources both need a small spike. Also: confirm Web vs Academic decision against a quick survey on GitHub Discussions if user-research signal exists (Focus Mode = Academic recommendation is HIGH-confidence by positioning, MEDIUM-confidence by validated user demand).

Phases with **standard patterns** (skip research-phase):

- **Phase 1 (Platform Hardening):** every item is a well-documented fix with reference impl in `CONCERNS.md` or the cited GitHub issues.
- **Phase 4 (Sessions + history + migrations):** `PRAGMA user_version` pattern has at least four working reference implementations cited in `PITFALLS.md` sources.
- **Phase 6 (Docs):** mechanical.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Verified against official PyPI listings, SDK changelogs, and 2026 benchmarks. Only MEDIUM area is the SearXNG opt-in adapter (recommended pattern but not user-validated demand). |
| Features | HIGH for table stakes and anti-features (Perplexity / Perplexica / OpenAI Deep Research / Tavily / Codex CLI feature sets are well-documented). MEDIUM for SearchMuse-specific differentiators (extrapolated from positioning, not user-validated). HIGH for terminal-rendering specifics (OSC 8 + Rich well-established). |
| Architecture | HIGH (codebase facts — read directly from `src/`, `.planning/codebase/`). MEDIUM for ecosystem streaming-pattern references but corroborated across OpenAI / Anthropic / Ollama / LlamaIndex / LangChain / Instructor (all converge on dual-method). |
| Pitfalls | HIGH — most pitfalls grounded in the project's own `CONCERNS.md` and `009_limitations.md`; ecosystem patterns verified via multiple 2025-2026 sources (Brave Comet IPI report, Perplexity BrowseSafe paper, Lasso 36% bypass, langchain DDG breakage issue, Rich author's streaming-markdown writeup, HalluLens hallucination benchmark, multiple `user_version` migration references). |

**Overall confidence:** HIGH

### Gaps to Address

- **Focus Mode = Academic is HIGH-confidence by positioning evidence but MEDIUM-confidence by user-validated demand.** A two-question survey on the SearchMuse GitHub Discussions before Phase 5 kickoff would de-risk cheaply. Phase 5 planning should run a small survey or accept the positioning-based call explicitly.
- **Quick Answer latency target of "< 5s first token" is an extrapolation** from Perplexity Sonar's 2.1s + a local Ollama 7-8B budget. Must be benchmarked on real hardware in Phase 2 and the target adjusted publicly if it doesn't hold.
- **Differentiator demand is unvalidated.** Privacy receipt, content hash, evidence-chain inspector, trace mode are reasoned from Core Value but not user-tested. Ship the cheapest (privacy receipt, content hash) first as low-risk signals; let GitHub issue volume gate the rest.
- **Local model parity eval baseline doesn't exist yet.** First time `make eval` runs against `ollama mistral`, the result *is* the baseline. Pre-Phase 2 spike to draft 10-20 Q/A/expected-source fixtures.
- **OpenAlex API stability post-Feb-2026 key requirement** — recent change, behaviour in the wild at our usage scale is unverified. Phase 5 spike should hit the real API with the wrapper before designing the adapter in earnest.
- **No published 1-line `safe_tail` reference implementation** — multiple projects (richify, Pydantic AI examples, willmcgugan/streaming-markdown) solve it slightly differently. Phase 2 spike to pick a concrete one.

---

## Sources

### Primary (HIGH confidence — this codebase)

- `.planning/PROJECT.md` — milestone scope, constraints, Key Decisions
- `.planning/codebase/ARCHITECTURE.md` / `STRUCTURE.md` / `INTEGRATIONS.md` / `CONVENTIONS.md` / `CONCERNS.md` / `STACK.md`
- `src/searchmuse/application/search_orchestrator.py`, `ports/llm_port.py`, `ports/chat_repository_port.py`, `application/progress.py`, `adapters/llm/prompts.py`
- `docs/001_functional/009_limitations.md`, `docs/002_technical/009_security.md`

### Primary (HIGH confidence — research files, full citations therein)

- `.planning/research/STACK.md` — official PyPI / SDK / vendor docs for `ollama`, `anthropic`, `openai`, `google-genai`, `rich`, `ddgs`, `pyalex`, `instructor`, `aiosqlite`, OpenAlex, SearXNG
- `.planning/research/FEATURES.md` — Perplexity / Perplexica / OpenAI Deep Research / Tavily / Codex CLI / chatgpt-cli official docs and blog posts
- `.planning/research/ARCHITECTURE.md` — OpenAI / Anthropic / Ollama / LlamaIndex / LangChain / Instructor official docs (all converge on dual-method streaming pattern)
- `.planning/research/PITFALLS.md` — Brave Comet IPI blog, Perplexity BrowseSafe paper + arXiv:2511.20597, Lakera IPI taxonomy, Lasso BrowseSafe bypass, langchain-ai/langchain#31892, Rich author's streaming-markdown writeup, gianlucatruda/richify, HalluLens benchmark (arXiv:2504.17550), FACTUM citation-hallucination paper (arXiv:2601.05866), eskerda / levlaz / gluer.org `PRAGMA user_version` references

### Secondary (MEDIUM confidence — agentic-search benchmarks, ecosystem patterns)

- aimultiple "Agentic Search Benchmark 2026"; Firecrawl "Brave Search API alternatives"; Brave API comparison guide
- IntuitionLabs "OpenAlex vs Semantic Scholar vs PubMed" and "Research Paper APIs 2026"
- Pydantic AI Stream Markdown example; HN "Preventing Flash of Incomplete Markdown"; Chrome devs "Best practices to render streamed LLM responses"
- Google ADK Loop agents docs (iterative-agent stop criteria)

### Tertiary (LOW confidence — needs validation during implementation)

- Focus Mode = Academic user demand (positioning-based, not survey-validated — see Gaps)
- Quick Answer < 5s first-token target (extrapolation — must benchmark)
- Differentiator demand for evidence-chain / privacy receipt / content hash (reasoned, not validated)

---

*Research completed: 2026-05-18*
*Ready for roadmap: yes*
