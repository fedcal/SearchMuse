# Requirements: SearchMuse — v0.2 "Perplexity-like CLI Foundation"

**Defined:** 2026-05-18
**Milestone:** v0.2 (first Perplexity-like milestone; subsequent milestones cover web/API/Deep Research/multi-Focus)
**Core Value:** Risposte web con citazioni verificabili, generate da modelli locali (Ollama) senza che query, prompt o documenti scaricati lascino la macchina dell'utente.

## v1 Requirements

Requirements for this milestone (v0.2). Each maps to exactly one phase in `ROADMAP.md`.

### Platform Hardening (PLAT)

Pre-condizioni invisibili agli utenti, indispensabili per non sabotare ogni fase successiva.

- [ ] **PLAT-01**: `duckduckgo-search` rimpiazzato da `ddgs >= 9.14.4`; adapter esistente continua a funzionare senza regressioni
- [ ] **PLAT-02**: SearchPort acquisisce un'astrazione multi-engine con fallback configurabile (almeno 2 backend selezionabili da config)
- [ ] **PLAT-03**: Politica `robots.txt` esplicita e configurabile (`fail_open` vs `fail_closed`) applicata a tutti i fetch (sia httpx sia playwright)
- [ ] **PLAT-04**: Rate limiting centralizzato per dominio con backoff esponenziale, condiviso tra adapter di scraping
- [ ] **PLAT-05**: Schema SQLite versionato con `PRAGMA user_version` e runner di migrazioni idempotente eseguito all'avvio
- [ ] **PLAT-06**: `instructor >= 1.15.1` integrato come dipendenza core per output strutturati LLM; sostituisce parsing regex fragile in coverage scoring
- [ ] **PLAT-07**: Bump dipendenze LLM: `ollama >= 0.6.2`, `anthropic >= 0.40`, `openai >= 1.55`, `google-genai >= 1.10`, `rich >= 13.7`, `pydantic >= 2.8`

### Domain Extensions (DOM)

Tipi e port nuovi che reggono tutta la milestone, in pura aggiunta (nessun breaking change).

- [ ] **DOM-01**: Value object `FocusMode` nel layer `domain/` con registry per modes attivi
- [ ] **DOM-02**: Value object `StopCriteria` (immutabile, frozen) con metodo `should_stop(state, elapsed) -> (bool, reason)` ispezionabile
- [ ] **DOM-03**: Tipo `LLMChunk` per i token streaming, con campi `text`, `is_final`, metadata opzionale
- [ ] **DOM-04**: Tipo `StrategyEvent` (union: `ProgressEvent`, `TokenEvent`, `CitationDiscoveredEvent`, `SearchResultEvent`) per eventi dall'orchestrator alla CLI
- [ ] **DOM-05**: Port `SearchStrategyPort` con metodo `async run(query, context) -> AsyncIterator[StrategyEvent]`

### Streaming & Citations (STREAM)

L'esperienza visibile: l'utente vede la risposta nascere token per token con citazioni navigabili.

- [ ] **STREAM-01**: `LLMPort` esposto con nuovo metodo `async stream_synthesize_answer(...) -> AsyncIterator[LLMChunk]` accanto al `synthesize_answer` esistente (additivo, non breaking)
- [ ] **STREAM-02**: Adapter Ollama implementa streaming nativo via `AsyncClient`
- [ ] **STREAM-03**: Adapter Anthropic / OpenAI / Gemini implementano streaming nativo via SDK ufficiali (fallback a batch-then-yield se l'utente disabilita streaming)
- [ ] **STREAM-04**: CLI consuma `AsyncIterator[StrategyEvent]` e renderizza token-by-token con `rich.live.Live` + Markdown progressivo
- [ ] **STREAM-05**: Helper `safe_tail()` evita flicker di Markdown durante stream (chiude `**`, backtick, code fence pendenti prima di ogni `Live.update`)
- [ ] **STREAM-06**: Citazioni inline `[N]` renderizzate come hyperlink OSC 8 quando il terminale lo supporta, fallback a testo + pannello fonti separato altrimenti
- [ ] **STREAM-07**: Pannello fonti sotto la risposta con titolo, dominio, URL completo e snippet di contesto per ogni `[N]` referenziata

### Search Modes (SEARCH)

Le due modalità di ricerca utente-visibili.

- [ ] **SEARCH-01**: Comando `searchmuse search "query" --quick` esegue Quick Answer: massimo 1-2 fonti, ≤ 5 secondi al primo token su hardware consumer con modello locale 7-8B
- [ ] **SEARCH-02**: Comando `searchmuse search "query"` (default) esegue Pro Search v2 iterativa
- [ ] **SEARCH-03**: `SearchStrategyPort` ha due implementazioni: `QuickAnswerStrategy` e `IterativeSearchStrategy` (refactor del loop esistente, behavior-preserving)
- [ ] **SEARCH-04**: `IterativeSearchStrategy` usa `instructor` + Pydantic models per scoring di coverage (sostituisce regex `_parse_coverage_score`)
- [ ] **SEARCH-05**: Stop criteria di Pro Search rese esplicite e visibili: alla fine compare riga "Stopped: coverage 0.78 ≥ 0.70 threshold" (o "max iterations", "min sources reached", ecc.)
- [ ] **SEARCH-06**: Eventi di progresso per iterazione emessi durante la Pro Search (`ProgressEvent` con iteration N, fonti trovate, score corrente)
- [ ] **SEARCH-07**: Cap massimo iterazioni e cap budget di tempo configurabili da `config/`, default sicuri (no loop infiniti)

### Verifiability (VERIFY)

I 3 differenziatori "cheap & high-signal" rispetto a Perplexity, coerenti con la verifiability-half del Core Value.

- [ ] **VERIFY-01**: Hash SHA-256 del contenuto estratto salvato accanto a ogni citazione; comando `searchmuse verify <session_id>` rileva fonti modificate dopo la citazione
- [ ] **VERIFY-02**: Estratto testuale (1-3 frasi) della porzione che supporta la claim salvato per ogni citazione, ispezionabile via `history`
- [ ] **VERIFY-03**: Comando `searchmuse explain <session_id>` mostra la evidence chain: iterazioni Pro Search, score di coverage, query raffinate, fonti scartate con motivo
- [ ] **VERIFY-04**: Footer "privacy receipt" stampato alla fine di ogni risposta non-streaming (e su richiesta in streaming): elenca modello usato, search backend, numero richieste rete, se è uscito qualcosa verso cloud (es. provider opt-in)

### Sessions & History (SESSION)

Persistenza e navigazione delle conversazioni multi-turn.

- [ ] **SESSION-01**: Schema `chat_messages` esteso additivamente per memorizzare citazioni, focus mode, modello, stop reason (no nuova entità `Session` parallela: si riusa `ChatSession`/`ChatMessage` esistenti)
- [ ] **SESSION-02**: Nuova tabella `message_citations` (FK su messaggio) per N citazioni per messaggio con `url`, `title`, `domain`, `content_hash`, `excerpt`, `iteration`
- [ ] **SESSION-03**: Sessione persistita automaticamente per ogni invocazione di `searchmuse search` e per ogni turno del REPL
- [ ] **SESSION-04**: Comando `searchmuse history` elenca sessioni recenti (id breve, titolo, timestamp, query iniziale, n.messaggi, focus mode)
- [ ] **SESSION-05**: Comando `searchmuse history show <session_id>` re-renderizza la conversazione con citazioni e privacy receipt
- [ ] **SESSION-06**: Comando `searchmuse history resume <session_id>` riapre la sessione nel REPL come contesto multi-turn
- [ ] **SESSION-07**: Auto-titling rule-based delle sessioni (prime N parole della query), comando `searchmuse history rename <id> "<titolo>"` per override
- [ ] **SESSION-08**: Comando `searchmuse history delete <session_id>` rimuove sessione e citazioni collegate (cascade)

### Focus Mode v1 — Academic (FOCUS)

Una sola modalità tematica nel milestone, sceglie Academic per validare il pattern e sfruttare il differenziatore privacy/verifiability.

- [ ] **FOCUS-01**: Default focus = `web` (comportamento attuale, retro-compatibile)
- [ ] **FOCUS-02**: Nuovo focus `academic` selezionabile via `--focus academic` su `search` e configurabile come default per sessioni REPL
- [ ] **FOCUS-03**: Focus `academic` usa un adapter di ricerca dedicato basato su OpenAlex via `pyalex >= 0.21` (extra `[academic]` opzionale)
- [ ] **FOCUS-04**: Focus `academic` usa un prompt pack dedicato (sintesi accademica, citazioni con autori/anno/venue oltre a URL)
- [ ] **FOCUS-05**: Pannello fonti in modalità academic mostra autori, anno, venue, DOI quando disponibili
- [ ] **FOCUS-06**: OpenAlex API key gestita dallo stesso resolver del provider LLM (`api_key_resolver.py`), graceful error se mancante con istruzioni
- [ ] **FOCUS-07**: Helper di "abstract reconstruction" da `abstract_inverted_index` di OpenAlex (campo non testuale → string)

### Test Infrastructure (TEST)

Senza test infrastructure adeguata, ogni cambio di adapter rompe la CI o costa troppo.

- [ ] **TEST-01**: Fixture cassette-based per le risposte LLM (registrazione/replay deterministico) — `pytest-vcr` o equivalente
- [ ] **TEST-02**: Eval harness minimale eseguibile in locale contro Ollama reale con modello 7-8B (10-20 query benchmark), separato dalla unit test suite
- [ ] **TEST-03**: Snapshot test della Pro Search iterativa esistente per garantire behavior-preserving refactor in SEARCH-03
- [ ] **TEST-04**: Test di prompt-injection con corpus minimo (pagine fittizie con payload), verifica che il fence di sicurezza non si rompa
- [ ] **TEST-05**: Coverage gate ≥ 80% mantenuto su tutto il codice nuovo

### Documentation (DOCS)

La documentazione MkDocs già pubblicata su GitHub Pages deve riflettere le nuove capability.

- [ ] **DOCS-01**: Pagina "Streaming & Citations" (EN + IT) con screenshot/cast del nuovo rendering
- [ ] **DOCS-02**: Pagina "Search Modes" (EN + IT) con confronto Quick vs Pro, esempi e tempi attesi
- [ ] **DOCS-03**: Pagina "Sessions & History" (EN + IT) con tutti i sotto-comandi `history`
- [ ] **DOCS-04**: Pagina "Focus Mode: Academic" (EN + IT) con istruzioni per ottenere API key OpenAlex e uso
- [ ] **DOCS-05**: Pagina "Verifiability" (EN + IT) che spiega `verify`, `explain`, privacy receipt, content hash
- [ ] **DOCS-06**: README.md e README.it.md aggiornati con le nuove demo command (no stale screenshots)
- [ ] **DOCS-07**: CHANGELOG.md aggiornato con la voce v0.2 e migration notes per utenti pre-alpha esistenti
- [ ] **DOCS-08**: `mkdocs build --strict` passa pulito; workflow `docs-check.yml` verde su PR

## v2 Requirements

Deferred to milestones successivi (no in questo milestone). Tracciati per memoria.

### Web Surface

- **WEB-01**: FastAPI backend con endpoint REST per query (con SSE per streaming)
- **WEB-02**: Frontend separato (framework JS scelto da ricerca futura: React/Svelte/Vue/Solid)
- **WEB-03**: UX visivamente vicina a Perplexity: input centrato, risposta streaming, fonti laterali, follow-up
- **WEB-04**: Self-hosted via Docker, deploy locale single-user

### Deep Research

- **DEEP-01**: Modalità Deep Research che produce report strutturato a sezioni
- **DEEP-02**: 10-30+ fonti citate con gerarchia (primarie vs supporting)
- **DEEP-03**: Export del report in Markdown/HTML/PDF

### Additional Focus Modes

- **FOCUS-V2-01**: Focus `code` (GitHub / StackOverflow / docs tecniche)
- **FOCUS-V2-02**: Focus `news` (fonti news con filtraggio temporale)
- **FOCUS-V2-03**: Focus `docs` (documentazione tecnica software)

### Quick Answer Auto-Routing

- **AUTO-01**: Classifier LLM che decide Quick vs Pro in base alla query (oggi switch manuale)

### Follow-up Suggestions

- **FOLLOW-01**: Auto-generazione di 3-5 follow-up question dopo ogni risposta (alla Perplexity)

### Citation Verification Avanzata

- **CITE-V2-01**: NLI model locale per entailment claim ↔ excerpt (oggi solo content hash + match testuale)

### Search Backend Aggiuntivi

- **SEARCH-V2-01**: Adapter SearXNG self-hosted (opt-in, on-brand per "purist")
- **SEARCH-V2-02**: Adapter Brave Search API (opt-in)
- **SEARCH-V2-03**: Adapter Tavily / Exa per ricerca semantica

## Out of Scope

Esclusioni esplicite del milestone, motivate per prevenire scope creep.

| Feature | Reason |
|---------|--------|
| Web UI / frontend JS | Rimandato a milestone web; il motore CLI deve maturare prima |
| HTTP API pubblica / SSE | Rimandata; non esponiamo un'API instabile |
| Deep Research mode | Richiede UX e modello cost-budget dedicati; meglio nella surface web |
| Focus Modes multipli (oltre Academic) | Validare il pattern con una sola modalità prima di moltiplicare |
| TUI Textual full-screen | Scartato a favore della CLI Rich evoluta (vincolo di effort) |
| Multi-utente / account / auth | Tool locale single-user per design |
| Pagamento / SaaS hosting | Resta open source self-hosted, MIT |
| Telemetry / analytics | Anti-feature: viola Core Value privacy |
| Pubblicità / sponsor | Anti-feature: viola posizionamento e Core Value |
| Chat persona / personalità | Anti-feature: non aggiunge valore informativo |
| Single-LLM lock-in | Anti-feature: violerebbe il multi-provider già esistente |
| Auto-fact-checking LLM | SOTA 2026 troppo immaturo (Pitfall 2); rinviato a quando NLI locale sarà pronto |
| Export PDF nativo | Markdown export sufficiente per v0.2; PDF richiede dipendenze pesanti |
| Browser extension | Fuori scope CLI; eventualmente nella surface web |
| Mobile app | Fuori scope CLI |

## Traceability

Aggiornato dal roadmapper dopo la creazione di `ROADMAP.md`.

| Requirement | Phase | Status |
|-------------|-------|--------|
| PLAT-01 | TBD | Pending |
| PLAT-02 | TBD | Pending |
| PLAT-03 | TBD | Pending |
| PLAT-04 | TBD | Pending |
| PLAT-05 | TBD | Pending |
| PLAT-06 | TBD | Pending |
| PLAT-07 | TBD | Pending |
| DOM-01 | TBD | Pending |
| DOM-02 | TBD | Pending |
| DOM-03 | TBD | Pending |
| DOM-04 | TBD | Pending |
| DOM-05 | TBD | Pending |
| STREAM-01 | TBD | Pending |
| STREAM-02 | TBD | Pending |
| STREAM-03 | TBD | Pending |
| STREAM-04 | TBD | Pending |
| STREAM-05 | TBD | Pending |
| STREAM-06 | TBD | Pending |
| STREAM-07 | TBD | Pending |
| SEARCH-01 | TBD | Pending |
| SEARCH-02 | TBD | Pending |
| SEARCH-03 | TBD | Pending |
| SEARCH-04 | TBD | Pending |
| SEARCH-05 | TBD | Pending |
| SEARCH-06 | TBD | Pending |
| SEARCH-07 | TBD | Pending |
| VERIFY-01 | TBD | Pending |
| VERIFY-02 | TBD | Pending |
| VERIFY-03 | TBD | Pending |
| VERIFY-04 | TBD | Pending |
| SESSION-01 | TBD | Pending |
| SESSION-02 | TBD | Pending |
| SESSION-03 | TBD | Pending |
| SESSION-04 | TBD | Pending |
| SESSION-05 | TBD | Pending |
| SESSION-06 | TBD | Pending |
| SESSION-07 | TBD | Pending |
| SESSION-08 | TBD | Pending |
| FOCUS-01 | TBD | Pending |
| FOCUS-02 | TBD | Pending |
| FOCUS-03 | TBD | Pending |
| FOCUS-04 | TBD | Pending |
| FOCUS-05 | TBD | Pending |
| FOCUS-06 | TBD | Pending |
| FOCUS-07 | TBD | Pending |
| TEST-01 | TBD | Pending |
| TEST-02 | TBD | Pending |
| TEST-03 | TBD | Pending |
| TEST-04 | TBD | Pending |
| TEST-05 | TBD | Pending |
| DOCS-01 | TBD | Pending |
| DOCS-02 | TBD | Pending |
| DOCS-03 | TBD | Pending |
| DOCS-04 | TBD | Pending |
| DOCS-05 | TBD | Pending |
| DOCS-06 | TBD | Pending |
| DOCS-07 | TBD | Pending |
| DOCS-08 | TBD | Pending |

**Coverage:**
- v1 requirements: 58 total
- Mapped to phases: 0 (filled by roadmapper)
- Unmapped: 58 ⚠️ — to be resolved by `gsd-roadmapper`

---
*Requirements defined: 2026-05-18*
*Last updated: 2026-05-18 after initial definition (research-informed)*
