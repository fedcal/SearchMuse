# Formati di Input e Output

SearchMuse supporta una varietà di formati per permettere integrazione flessibile con altri tool e workflow.

---

## Input Formats

### 1. Stringa Semplice (Default)

**Uso**: Command line, script semplici

```bash
searchmuse "best Python web frameworks 2026"
```

**Proprietà**:
- Formato più intuitivo
- Automaticamente interpretato come query
- Opzioni default applicate

---

### 2. JSON Strutturato

**Uso**: API calls, automazione avanzata, configurazione complessa

```json
{
  "query": "best Python web frameworks 2026",
  "max_iterations": 3,
  "strategy": "comprehensive",
  "depth": "detailed",
  "include_sources": true,
  "output_format": "markdown"
}
```

**Proprietà Obbligatorie**:
- `query` (string): La query di ricerca

**Proprietà Opzionali**:
- `max_iterations` (int, default 3): Numero massimo di iterazioni (1-7)
- `strategy` (enum, default "balanced"):
  - `fast`: 1-2 iterazioni, speed prioritized
  - `balanced`: 3 iterazioni (default)
  - `comprehensive`: 4-5 iterazioni, quality prioritized
- `depth` (enum, default "standard"):
  - `quick`: 50-100 words summary
  - `standard`: 100-300 words summary
  - `detailed`: 300-500 words summary
  - `comprehensive`: 500+ words with aspects
- `include_sources` (bool, default true): Includi citazioni
- `output_format` (enum, default "markdown"):
  - `markdown`, `json`, `html`, `plaintext`
- `citation_format` (enum, default "markdown"):
  - `markdown`, `apa`, `mla`, `chicago`, `plaintext`
- `language` (string, default "en"):
  - Lingua per output (en, it, fr, de, es, pt)
- `timeout_seconds` (int, default 180): Timeout totale

**Esempi di Proprietà Opzionali Extra**:

```json
{
  "query": "electric cars range 2026",
  "max_iterations": 2,
  "strategy": "fast",
  "only_recent_results": true,
  "minimum_authority_score": 70,
  "exclude_domains": ["reddit.com", "quora.com"],
  "preferred_languages": ["en"],
  "quality_threshold": 75
}
```

---

### 3. File di Configurazione YAML

**Uso**: Batch processing, configurazione persistente

```yaml
# search_config.yaml
query: "best Python web frameworks 2026"

research:
  max_iterations: 3
  strategy: "comprehensive"
  depth: "detailed"

output:
  format: "markdown"
  citation_format: "apa"
  include_metadata: true

quality:
  minimum_coverage: 80
  minimum_relevance: 75
  minimum_authority: 60

filtering:
  exclude_domains:
    - "reddit.com"
    - "stackoverflow.com"
  preferred_domains:
    - "github.com"
    - "official-docs"
  recency_days: 365

performance:
  timeout_seconds: 300
  max_parallel_scraping: 3
  cache_results: true
```

**Uso**:
```bash
searchmuse -c search_config.yaml
```

---

## Output Formats

### 1. Markdown (Default)

**Uso**: Blog, GitHub, documentazione, readability ottima

```markdown
# Best Python Web Frameworks 2026

## Overview
FastAPI has emerged as the leading Python web framework for 2026,
gaining significant adoption in enterprise environments due to its
high performance and modern async support[(1)].

## Key Frameworks

### 1. FastAPI
- **Performance**: 2000+ requests/sec
- **Async Support**: Full native async/await
- **Learning Curve**: Moderate
- **Production Ready**: Yes, enterprise adoption increasing[(2)]

### 2. Django
- **Maturity**: 20+ years development
- **Learning Curve**: Steep, comprehensive
- **Community**: Largest Python web framework community[(3)]
- **Suitable For**: Large applications, rapid development

## Comparison Table

| Framework | Performance | Maturity | Community | Best For |
|-----------|------------|----------|-----------|----------|
| FastAPI | Excellent | Newer | Growing | Performance-critical APIs |
| Django | Good | Excellent | Massive | Full-stack applications |
| Flask | Good | Mature | Large | Lightweight microservices |

## Cited Sources

1. [FastAPI 2026 Performance Benchmarks](https://example.com/benchmarks)
   - Source: benchmarks.io
   - Accessed: Feb 28, 2026

2. [Enterprise FastAPI Adoption 2026](https://example.com/adoption)
   - Source: tech-reports.com
   - Accessed: Feb 28, 2026

3. [Django Community Statistics](https://example.com/django-stats)
   - Source: djangoproject.com
   - Accessed: Feb 28, 2026
```

**Vantaggi**:
- Leggibile sia per umani che per machine
- Facile da integrare in docs
- Supporta tabelle, liste, code blocks
- Citazioni inline

---

### 2. JSON Strutturato

**Uso**: API responses, data pipelines, elaborazione programmatica

```json
{
  "success": true,
  "data": {
    "query": "best Python web frameworks 2026",
    "summary": {
      "text": "FastAPI has emerged as the leading Python web framework...",
      "word_count": 287,
      "aspects_covered": 5
    },
    "aspects": [
      {
        "name": "Performance",
        "description": "FastAPI achieves 2000+ requests/sec...",
        "sources": [
          {
            "url": "https://example.com/benchmarks",
            "title": "FastAPI 2026 Benchmarks",
            "accessed": "2026-02-28"
          }
        ]
      },
      {
        "name": "Community",
        "description": "Django has the largest community...",
        "sources": [...]
      }
    ],
    "sources": [
      {
        "id": "src-001",
        "url": "https://example.com/benchmarks",
        "title": "FastAPI Performance Benchmarks 2026",
        "author": "Jane Smith",
        "published": "2026-02-15",
        "accessed": "2026-02-28",
        "authority_score": 85,
        "relevance_score": 92,
        "context": "FastAPI achieves 2000+ requests per second..."
      }
    ],
    "metadata": {
      "total_sources": 8,
      "coverage_score": 82,
      "quality_score": 85,
      "iterations": 2,
      "total_time_seconds": 147,
      "research_completed": "2026-02-28T14:32:15Z"
    }
  },
  "error": null
}
```

**Schema**:
```json
{
  "success": boolean,
  "data": {
    "query": string,
    "summary": {
      "text": string,
      "word_count": integer,
      "aspects_covered": integer
    },
    "aspects": [
      {
        "name": string,
        "description": string,
        "sources": [reference_array]
      }
    ],
    "sources": [
      {
        "id": string,
        "url": string,
        "title": string,
        "author": string,
        "published": iso_date,
        "accessed": iso_date,
        "authority_score": 0-100,
        "relevance_score": 0-100,
        "context": string
      }
    ],
    "metadata": {
      "total_sources": integer,
      "coverage_score": 0-100,
      "quality_score": 0-100,
      "iterations": integer,
      "total_time_seconds": number,
      "research_completed": iso_datetime
    }
  },
  "error": string_or_null
}
```

---

### 3. HTML

**Uso**: Embedding in web pages, newsletter

```html
<div class="searchmuse-result">
  <h1>Best Python Web Frameworks 2026</h1>

  <div class="summary">
    <p>FastAPI has emerged as the leading Python web framework for 2026,
    gaining significant adoption in enterprise environments due to its
    high performance and modern async support<a href="#cite-1">[1]</a>.</p>
  </div>

  <section class="aspects">
    <div class="aspect">
      <h2>Performance</h2>
      <p>FastAPI achieves excellent performance with 2000+ requests per
      second<a href="#cite-2">[2]</a>.</p>
    </div>

    <div class="aspect">
      <h2>Community</h2>
      <p>Django maintains the largest Python web framework community...</p>
    </div>
  </section>

  <section class="sources">
    <h2>Sources</h2>
    <ol>
      <li id="cite-1">
        <a href="https://example.com/benchmarks">FastAPI 2026 Performance</a>
        - example.com | Accessed: Feb 28, 2026
      </li>
      <li id="cite-2">
        <a href="https://example.com/adoption">Enterprise Adoption</a>
        - tech-reports.com | Accessed: Feb 28, 2026
      </li>
    </ol>
  </section>

  <div class="metadata">
    <p>Quality Score: 85/100 | Coverage: 82% | Sources: 8</p>
  </div>
</div>
```

---

### 4. Plain Text

**Uso**: Email, documenti semplici, export basic

```
BEST PYTHON WEB FRAMEWORKS 2026

FastAPI has emerged as the leading Python web framework for 2026,
gaining significant adoption in enterprise environments due to its
high performance and modern async support.

KEY FRAMEWORKS:

1. FastAPI
   Performance: 2000+ requests/sec
   Async Support: Full native async/await
   Learning Curve: Moderate
   Production Ready: Yes

2. Django
   Maturity: 20+ years development
   Learning Curve: Steep
   Community: Largest Python web framework community
   Best For: Large applications

3. Flask
   Maturity: Mature framework
   Philosophy: Lightweight and flexible
   Best For: Microservices, APIs

CITED SOURCES:

1. FastAPI 2026 Performance Benchmarks
   https://example.com/benchmarks
   Source: benchmarks.io
   Accessed: Feb 28, 2026

2. Enterprise FastAPI Adoption 2026
   https://example.com/adoption
   Source: tech-reports.com
   Accessed: Feb 28, 2026

METADATA:
Quality Score: 85/100
Coverage: 82%
Total Sources: 8
Research Time: 147 seconds
```

---

## Error Formats

Quando un errore occorre, SearchMuse ritorna:

### JSON Error Response

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "SEARCH_FAILED",
    "message": "Unable to find sufficient results for query",
    "details": {
      "query": "extremely obscure topic xyz123",
      "coverage_achieved": 35,
      "coverage_required": 80,
      "sources_found": 2,
      "reason": "Query too specific, insufficient web coverage"
    },
    "timestamp": "2026-02-28T14:32:15Z"
  }
}
```

### Error Codes

```
SUCCESS_PARTIAL
  - Ricerca completata ma coverage < 80%
  - Risultati comunque restituiti

SEARCH_FAILED
  - Nessun risultato trovato

TIMEOUT
  - Ricerca ha ecceduto tempo massimo

NETWORK_ERROR
  - Errore di connessione durante scraping

INVALID_QUERY
  - Query non valida o malformata

LLM_ERROR
  - Errore nel modello LLM (timeout, crash)

RATE_LIMITED
  - Troppi request, backoff necessario

UNSUPPORTED_LANGUAGE
  - Lingua richiesta non supportata
```

---

## Streaming

Per ricerche lunghe, SearchMuse supporta **Server-Sent Events** streaming:

```bash
curl -N http://localhost:8000/api/search/stream \
  -H "Content-Type: application/json" \
  -d '{"query": "Python frameworks"}'
```

**Stream Events**:

```
data: {"event": "search_started", "query": "Python frameworks"}

data: {"event": "iteration", "iteration": 1, "query_used": "best Python frameworks 2026"}

data: {"event": "scraping", "urls_found": 10, "progress": 0.2}

data: {"event": "scraping", "urls_found": 10, "progress": 1.0, "successful": 9}

data: {"event": "iteration_complete", "coverage": 65, "relevance": 75}

data: {"event": "iteration", "iteration": 2, "query_used": "Django FastAPI comparison"}

data: {"event": "scraping", "urls_found": 8, "progress": 1.0, "successful": 7}

data: {"event": "iteration_complete", "coverage": 85, "relevance": 88}

data: {"event": "research_complete", "total_time": 147, "quality_score": 85}

data: {"event": "result_summary", "word_count": 287, "sources": 8}

data: {"event": "complete", "success": true}
```

---

## Esempi Pratici

### Esempio 1: Query Semplice da CLI

```bash
$ searchmuse "electric vehicles range 2026"

# Output (default Markdown)
# Best Electric Vehicles Range 2026
# ...
```

### Esempio 2: JSON Input da API

```bash
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Python web frameworks comparison",
    "max_iterations": 2,
    "output_format": "json",
    "depth": "standard"
  }'
```

**Response**:
```json
{
  "success": true,
  "data": {
    "query": "Python web frameworks comparison",
    "summary": { ... },
    "metadata": { ... }
  }
}
```

### Esempio 3: File YAML Configuration

```bash
$ cat > research.yaml << EOF
query: "machine learning trends 2026"
research:
  max_iterations: 3
  strategy: comprehensive
output:
  format: markdown
  citation_format: apa
EOF

$ searchmuse -c research.yaml > research_output.md
```

### Esempio 4: Streaming per Long Research

```bash
$ curl -N http://localhost:8000/api/search/stream \
  -H "Content-Type: application/json" \
  -d '{"query": "AI governance 2026", "max_iterations": 4}' \
  | jq -r '.event'

# Output
# search_started
# iteration
# scraping
# iteration_complete
# iteration
# ...
# complete
```

---

**Versione**: 1.0
**Ultimo aggiornamento**: 2026-02-28
