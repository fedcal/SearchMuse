# SearchMuse

## What This Is

SearchMuse è un assistente di ricerca web intelligente, open source e locale-first, pensato come alternativa a Perplexity per chi non vuole rinunciare a privacy, profondità di indagine e controllo sulla propria pipeline. L'utente di riferimento sono ricercatori, giornalisti, sviluppatori e analisti che fanno ricerca seria e vogliono citazioni verificabili senza affidare i propri dati e prompt a un servizio chiuso. Oggi è pre-alpha e funziona come CLI Python con architettura esagonale, ricerca iterativa LLM-driven e citazioni con fonti.

## Core Value

**Risposte web con citazioni verificabili, generate da modelli locali (Ollama) senza che query, prompt o documenti scaricati lascino la macchina dell'utente.** Se tutto il resto fallisce, questa singola promessa — qualità di risposta paragonabile a Perplexity con privacy totale e fonti audit-ready — deve restare vera.

## Requirements

### Validated

<!-- Capabilities già presenti nella codebase pre-alpha, ereditate come base. -->

- ✓ CLI typer-based con comando `searchmuse` e REPL interattivo — esistente
- ✓ Architettura esagonale (ports/adapters, domain, application, infrastructure) — esistente
- ✓ Adapter LLM per Ollama (locale, default) — esistente
- ✓ Adapter LLM opzionali per Claude, OpenAI, Gemini (opt-in via extras) — esistente
- ✓ Ricerca via DuckDuckGo + scraping con httpx/trafilatura/readability-lxml — esistente
- ✓ Algoritmo di ricerca iterativa con raffinamento LLM-driven (base di Pro Search) — esistente
- ✓ Sistema di citazione con numeri e URL verificabili — esistente
- ✓ Persistenza SQLite via aiosqlite — esistente
- ✓ Tipizzazione strict mypy e coverage gate 80% via pytest — esistente
- ✓ Documentazione MkDocs pubblicata su GitHub Pages — esistente

### Active

<!-- Scope del primo milestone "v0.2 — Perplexity-like CLI Foundation". Ipotesi finché non spedite. -->

- [ ] **Streaming token-by-token nella CLI** durante la generazione della risposta (oggi probabilmente batch)
- [ ] **Citazioni inline rich** nel testo (es. `[1]`, `[2]` cliccabili in terminali compatibili, con pannello fonti formattato Rich)
- [ ] **Quick Answer mode** — risposta veloce 1-2 fonti per query semplici, opposta alla Pro Search iterativa
- [ ] **Pro / Iterative Search v2** — rifinire l'algoritmo esistente con stop-criteria espliciti e ispezione della catena di evidenza
- [ ] **Persistenza sessioni** — conversazione multi-turn salvata in SQLite, riapribile e ispezionabile
- [ ] **Focus Mode v1** — una modalità tematica (Academic o Web, decisione data alla research) che filtra fonti e prompt
- [ ] **Comando `searchmuse history`** per esplorare e riaprire sessioni passate
- [ ] **Documentazione utente** della nuova UX su MkDocs/GitHub Pages, EN + IT

### Out of Scope

<!-- Esclusioni esplicite del primo milestone, con motivazione per evitare scope creep. -->

- Web app / frontend JS — rimandato a milestone successivo, qui niente UI grafica
- API HTTP / SSE pubblica — rimandata; il "motore" deve maturare prima di essere esposto
- Deep Research mode (report lungo strutturato) — rimandato al milestone web, richiede UX dedicata
- Focus Modes multipli (Code, News, Docs in aggiunta al primo) — rimandati, una modalità tematica alla volta
- TUI Textual full-screen — alternativa scartata in favore della CLI Rich evoluta
- Multi-utente / account / auth — non pertinente a un tool locale single-user
- Pagamento / SaaS hosting — il progetto è e resta open source self-hosted

## Context

- **Stato attuale:** pre-alpha (`Development Status :: 2 - Pre-Alpha` in `pyproject.toml`). Codice esistente già mappato in `.planning/codebase/` (vedi `ARCHITECTURE.md`, `STACK.md`, `CONCERNS.md`).
- **Stack consolidato:** Python ≥ 3.11, hatchling, ruff, mypy strict, pytest + pytest-asyncio + pytest-cov, httpx[http2], playwright (opzionale), trafilatura, readability-lxml, beautifulsoup4, ollama, typer, rich, aiosqlite, duckduckgo-search.
- **Architettura:** hexagonal/ports-and-adapters già impostata; nuovi feature dovrebbero rispettare il pattern (vedi `.planning/codebase/ARCHITECTURE.md`).
- **CI/CD:** GitHub Actions con `ci.yml` (lint, type-check, test 3.11/3.12/3.13), `docs.yml` (deploy MkDocs), `docs-check.yml` (PR validation). GitHub Pages attivo per la documentazione.
- **Concorrenza di mercato:** Perplexity Pro (cloud, closed), Phind (focus dev), You.com, Kagi Assistant (cloud), oltre a soluzioni self-hosted minori (LocalGPT-style). SearchMuse si differenzia tenendo locale + open + estendibile come trade-off coerente.
- **Vincolo di effort reale:** ~5h/settimana, nessuna deadline. Le fasi devono essere piccole e indipendenti, parallelizzabili dove possibile, con commit atomici e niente dipendenze monolitiche.
- **Debiti tecnici noti:** vedi `.planning/codebase/CONCERNS.md` — coverage gaps in moduli non ancora testati, dipendenze pre-1.0 (`ddgs`, `ollama`, `duckduckgo-search`), browser binaries di playwright come dep opzionale pesante.

## Constraints

- **Tech stack**: Python ≥ 3.11, mypy strict, ruff, pytest, coverage ≥ 80%. Nessun cambio di linguaggio o di paradigma architetturale (resta esagonale).
- **Compatibility**: la CLI esistente `searchmuse search …` deve restare retro-compatibile o offrire un percorso di migrazione documentato.
- **Privacy**: nessuna telemetria; nessuna chiamata di rete non strettamente necessaria al fetch delle fonti e all'inferenza LLM scelta dall'utente.
- **Performance**: la Quick Answer deve restituire la prima fonte entro pochi secondi su hardware consumer con Ollama + modello 7-8B; la Pro Search può richiedere più tempo ma deve mostrare progresso continuo (streaming + log delle iterazioni).
- **Dependencies**: preferire dipendenze stabili; nuove dipendenze pre-1.0 vanno motivate; playwright resta opzionale.
- **Resources**: ~5h/settimana, niente deadline. Fasi piccole, indipendenti, ognuna deliverabile in 1-3 settimane di calendario.
- **Licenza**: MIT, open source, no SaaS lock-in.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Posizionamento "alternativa Perplexity locale-first" | Differenziazione netta vs Perplexity/Phind cloud; coerente con stack Ollama già presente | — Pending |
| Vision multi-pilastro (privacy + profondità + estendibilità + multi-fonte) come north star, ma rilascio per milestone successive | Scope tutto-subito incompatibile con ~5h/settimana; meglio spedire spesso valore incrementale | — Pending |
| Primo milestone resta CLI-only (no web, no API, no Deep Research) | Vincolo di effort; il motore deve maturare prima di esporre superfici nuove | — Pending |
| Locale-first con cloud opt-in (Ollama default, Claude/OpenAI/Gemini come extras esistenti) | Massima coerenza con Core Value; non rinuncia alla flessibilità per chi la vuole | — Pending |
| Architettura esagonale conservata | È già in piedi e supporta multi-adapter (LLM, search engine, scraper) — perfetto per estendibilità | ✓ Good |
| Una sola Focus Mode in v1 (scelta tra Academic e Web) | Validare il pattern Focus prima di moltiplicarlo | — Pending |
| Web frontend in milestone successivo userà FastAPI + framework JS separato (scelta JS da research) | Coerenza Python sul backend + libertà di scelta sul frontend | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-05-18 after initialization*
