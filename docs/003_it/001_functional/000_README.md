# Documentazione Funzionale SearchMuse - Italian Edition

Benvenuto nella documentazione funzionale di SearchMuse in italiano. Questa collezione di documenti descrive la visione, gli obiettivi, le funzionalità, l'architettura e la roadmap di SearchMuse.

---

## File Contenuti

### 1. **vision-and-goals.md**
Fondamenti filosofici e strategici di SearchMuse.

**Contenuti**:
- Visione del progetto
- Problemi che risolve
- Obiettivi principali (5 pillars)
- Principi di progettazione
- Non-obiettivi espliciti
- Metriche di successo

**Quando leggerlo**: Primo, per comprendere il "why" dietro SearchMuse

---

### 2. **use-cases.md**
Scenari reali di utilizzo con user stories e criteri di accettazione.

**Contenuti**:
- Persona: Alex il ricercatore curioso
- 5 casi d'uso principali:
  - Ricerca rapida di fatti
  - Ricerca approfondita
  - Confronto tecnologico
  - Revisione letteratura
  - Analisi tendenze
- User stories per ogni caso
- Criteri di accettazione
- Metriche di successo per caso

**Quando leggerlo**: Per capire come SearchMuse si integra nei workflow reali

---

### 3. **feature-specifications.md**
Descrizione dettagliata delle 6 feature principali con specifiche funzionali.

**Contenuti**:
- Feature 1: Ricerca Iterativa Intelligente
- Feature 2: Citazione Automatica delle Fonti
- Feature 3: Estrazione Intelligente del Contenuto
- Feature 4: Integrazione Modelli LLM Locali
- Feature 5: Scraping Multi-Strategia
- Feature 6: Sintesi Intelligente dei Risultati
- Diagramma Mermaid del flusso di ricerca

**Quando leggerlo**: Per comprendere come SearchMuse funziona, architettura alta livello

---

### 4. **search-refinement-algorithm.md**
Algoritmo core di ricerca iterativa con spiegazione dettagliata, matematica, e flowchart.

**Contenuti**:
- 9 passi dell'algoritmo:
  1. Parsing query
  2. Strategia LLM
  3. Ricerca DuckDuckGo
  4. Scraping multi-strategia
  5. Estrazione contenuto
  6. Valutazione rilevanza
  7. Valutazione copertura
  8. Decisione raffinamento
  9. Query raffinata
- Criteri di convergenza
- Formula Quality Score (5 componenti)
- Diagramma Mermaid flowchart
- Esempio esecuzione completa
- Ottimizzazioni e euristiche

**Quando leggerlo**: Per developers, architects, chi vuole capire il cuore di SearchMuse

---

### 5. **source-citation.md**
Sistema completo di citazione automatica e tracciabilità delle fonti.

**Contenuti**:
- Filosofia di citazione
- Modello dati per citazioni (JSON schema)
- 6 step del processo di estrazione citazione
- 6 formati di citazione supportati:
  - Markdown
  - HTML
  - APA
  - MLA
  - Chicago
  - Plain Text
- Gestione citazioni nelle sintesi
- Compliance e verifica
- Esempio end-to-end
- Best practices per utenti

**Quando leggerlo**: Quando usi SearchMuse per articoli/paper e devi citare correttamente

---

### 6. **supported-websites.md**
Categorie di siti supportati, livelli di supporto, strategie di scraping, come aggiungere nuovi siti.

**Contenuti**:
- 4 livelli di supporto (Ottimizzato > Buono > Limitato > Non supportato)
- 7 categorie di siti con success rates
- Algoritmo di selezione strategia
- Come aggiungere nuovo sito/categoria
- Conformità robots.txt e legale
- Limitazioni tecniche per categoria
- Statistiche di supporto (10k URL sample)

**Quando leggerlo**: Per capire quali siti funzionano bene, come contribuire migliori scraper

---

### 7. **llm-requirements.md**
Requisiti Ollama, modelli consigliati, hardware, parametri, prompt templates.

**Contenuti**:
- Panoramica Ollama e setup
- 5 modelli consigliati con specifiche dettagliate:
  - Mistral 7B (default)
  - Llama3 8B
  - Llama3 70B
  - Phi3 (edge)
  - Neural Chat (specialized)
- Selezione modello per caso d'uso
- Requisiti hardware (minimo, consigliato, ottimale)
- Parametri LLM ottimizzati per ogni operazione
- 4 prompt templates
- Monitoring performance
- Troubleshooting
- Configurazione SearchMuse

**Quando leggerlo**: Prima di installare/configurare SearchMuse, per scegliere modello

---

### 8. **input-output-formats.md**
Formati di input accettati e output supportati con esempi.

**Contenuti**:
- 3 formati input:
  - Stringa semplice
  - JSON strutturato
  - File YAML
- 4 formati output:
  - Markdown (default)
  - JSON strutturato
  - HTML
  - Plain text
- Error format
- Streaming (SSE) support
- 4 esempi pratici di utilizzo
- Schema JSON completo

**Quando leggerlo**: Quando integri SearchMuse in sistemi, per comprendere IO

---

### 9. **limitations.md**
Limitazioni chiare e oneste di SearchMuse, disclaimer di responsabilità.

**Contenuti**:
- Limitazioni di scope (what does well vs. doesn't)
- Limitazioni di qualità:
  - Qualità variabile fonti
  - Allucinazioni LLM
  - Recency di informazione
  - Incompletezza coverage web
- Limitazioni tecniche:
  - Context window LLM
  - Latency ricerca
  - Pulizia contenuto
- Limitazioni site-specifiche (social media, e-commerce, paywalled, etc.)
- Confronto con strumenti alternativi:
  - vs. Google Search
  - vs. ChatGPT
  - vs. Database accademici
- Disclaimer responsabilità
- Come segnalare problemi

**Quando leggerlo**: Prima di usare SearchMuse, per avere aspettative realistiche

---

### 10. **roadmap.md**
Piano di sviluppo versionate con timeline, features, e success criteria.

**Contenuti**:
- Metodologia semantic versioning
- v0.1.0 (MVP, Feb-Mar 2026) - In Development
- v0.2.0 (Iterative, Mar-May 2026) - Planned
- v0.3.0 (Polish, May-Jun 2026) - Planned
- v1.0.0 (Production, Jun-Jul 2026) - Planned
- Futuro post-v1.0 (v1.1-v3.0 ideation)
- Community roadmap input
- Fattori che impattano roadmap
- Version support matrix
- Migration paths
- Come stare aggiornato

**Quando leggerlo**: Quando vuoi sapere cosa viene next, o contribuire al progetto

---

## Come Navigare Questa Documentazione

### Se sei un Nuovo Utente
1. Leggi: **vision-and-goals.md** (capire il cosa e perché)
2. Leggi: **use-cases.md** (come si applica al tuo caso d'uso)
3. Leggi: **feature-specifications.md** (come funziona in pratica)
4. Leggi: **limitations.md** (aspettative realistiche)

### Se sei un Developer
1. Leggi: **feature-specifications.md** (architettura)
2. Leggi: **search-refinement-algorithm.md** (core logic)
3. Leggi: **supported-websites.md** (extensibility)
4. Leggi: **llm-requirements.md** (LLM integration)

### Se integri SearchMuse
1. Leggi: **input-output-formats.md** (interface contract)
2. Leggi: **llm-requirements.md** (setup)
3. Leggi: **limitations.md** (constraint awareness)

### Se contribuisci
1. Leggi tutto in questo ordine
2. Vedi: **roadmap.md** (priorità del progetto)
3. Apri GitHub issue con proposta
4. Attendi feedback maintainer

---

## Glossario Terminologia

| Termine | Significato |
|---------|------------|
| **Query** | Domanda o ricerca input dell'utente |
| **Iterazione** | Ciclo di search-evaluate-refine |
| **Coverage** | Percentuale di aspetti dell'argomento coperti |
| **Relevance** | Quanto risultato corrisponde alla query |
| **Scraping** | Estrazione automatica di contenuto da web |
| **LLM** | Large Language Model (modello di linguaggio) |
| **Ollama** | Runtime per eseguire LLM localmente |
| **Citazione** | Fonte di un'affermazione (URL, autore, data) |
| **Authority Score** | Valutazione affidabilità della fonte |
| **Convergenza** | Stato dove ricerca ha raggiunto qualità target |

---

## Convenzioni Della Documentazione

- **Italian Prose**: Testo è in italiano, professionale
- **English Code/Technical**: Tutti gli esempi di codice, comando, Mermaid diagram rimangono in English
- **Bold per Emphasis**: Concetti importanti sono in **bold**
- **Code Blocks**: Per configurazioni, JSON, comandi CLI
- **Tables**: Per comparazioni, matrices, reference data
- **Mermaid Diagrams**: Per flussi, architettura, algoritmi

---

## Changelog Della Documentazione

| Data | Versione | Cambiamento |
|------|----------|-----------|
| 2026-02-28 | 1.0 | Creazione iniziale (10 file) |

---

## Contribuire alla Documentazione

Se trovi errori, incompletezza, o suggerimenti:

1. **Semplice Fix**: Apri PR con correzione
2. **Grossa Revisione**: Apri issue first per discutere
3. **Nuova Sezione**: Discuti in community forum

Tutte le contribuzioni sono benvenute!

---

## Licenza

Questa documentazione è parte di SearchMuse, open source sotto MIT License.

---

**Versione Documentazione**: 1.0
**Data**: 2026-02-28
**Lingua**: Italian
**Maintainer**: SearchMuse Team
**Link Repository**: https://github.com/searchmuse/core
