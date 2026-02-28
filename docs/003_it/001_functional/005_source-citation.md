# Citazione delle Fonti e Tracciabilità

## Filosofia della Citazione

SearchMuse opera sul principio che **ogni affermazione di fatto deve essere tracciabile alla sua fonte originale**. Questo non è solo un requisito accademico ma fondamentale per:

- **Verificabilità**: Lettori possono controllare l'informazione in autonomia
- **Accountability**: Creatori di contenuto mantengono responsabilità per claim
- **Qualità**: Informazioni non citate sono sospette
- **Rispetto Intellettuale**: Riconoscimento del lavoro altrui

Nessun fact dovrebbe mai essere presentato senza una chiara traccia verso la fonte originale.

---

## Modello Dati per Citazioni

Ogni citazione è rappresentata come:

```json
{
  "id": "uuid",
  "type": "citation",
  "source": {
    "url": "https://example.com/article",
    "title": "Article Title",
    "domain": "example.com",
    "author": "John Doe",
    "publication_date": "2026-02-20",
    "access_date": "2026-02-28",
    "accessed_via": "html_parser",
    "http_status": 200
  },
  "content": {
    "extracted_text": "The full sentence or paragraph extracted",
    "start_position": 1234,
    "end_position": 1456,
    "context_before": "Previous 30 words...",
    "context_after": "...Next 30 words"
  },
  "metadata": {
    "confidence_score": 0.95,
    "relevance_score": 85,
    "extraction_method": "trafilatura",
    "source_authority": "high",
    "language": "en"
  },
  "formatting": {
    "markdown": "[Article Title](https://example.com/article)",
    "apa": "Doe, J. (2026). Article title. Retrieved February 28, 2026, from https://example.com/article",
    "mla": "Doe, John. \"Article Title.\" Example, accessed Feb. 28, 2026, example.com/article.",
    "chicago": "Doe, John. \"Article Title.\" Accessed February 28, 2026. https://example.com/article."
  }
}
```

---

## Processo di Estrazione della Citazione

### Step 1: Cattura del Metadato della Fonte

Durante lo scraping, catturiamo:

**Da HTML Meta Tags**:
```html
<meta property="og:title" content="Article Title">
<meta property="og:url" content="https://example.com/article">
<meta name="author" content="John Doe">
<meta property="article:published_time" content="2026-02-20">
<meta name="description" content="Article description">
```

**Da Structured Data**:
```json
{
  "@type": "NewsArticle",
  "headline": "Article Title",
  "author": {"@type": "Person", "name": "John Doe"},
  "datePublished": "2026-02-20",
  "dateModified": "2026-02-25"
}
```

**Fallback per pagine semplici**:
- Titolo da `<title>` tag
- URL canonico da `<link rel="canonical">`
- Author da primo byline testuale
- Date da pagina URL pattern (se datata)

### Step 2: Estrazione del Contesto

Quando un fatto è identificato nei risultati aggregati:

1. **Localize**: Trova esattamente dove appare nel contenuto estratto
2. **Extract Context**: 30-50 parole prima e dopo
3. **Validation**: Assicura che il contesto è rappresentativo
4. **Confidence Score**: 0-100 su quanto bene il contesto rappresenta il fact

### Step 3: Validazione URL

```
1. Parse URL per validità strutturale
2. Test accessibilità (HTTP HEAD request)
3. Check redirect chains
4. Canonicalize URL (remove tracking params)
5. Verify content still exists (se possibile)
6. Get final HTTP status
```

Se URL ritorna 404, tenta:
- Wayback Machine snapshot
- Archive.org alternative
- Marchia come "archived/unavailable"

### Step 4: Estrazione Autore

Priorità:

```
1. <meta name="author"> tag
2. Schema.org author field
3. First byline in content
4. Copyright footer attribution
5. Domain admin contact (fallback)
6. Anonymous (if truly unknown)
```

### Step 5: Determinazione Data

**Priorità per data di pubblicazione**:
```
1. og:published_time meta tag
2. article:published_time schema
3. datePublished structured data
4. Date nel URL path (YYYY-MM-DD pattern)
5. Last-Modified HTTP header
6. Meta date nel testo
7. Oggi (fallback)
```

**Nota**: Registra sempre la data di accesso (quando SearchMuse ha scraping) separatamente.

### Step 6: Scoring di Autorità della Fonte

Determina l'affidabilità della fonte:

```
Authority Score Factors:

+ 25 pts: Dominio .edu o .gov
+ 15 pts: HTTPS secure connection
+ 15 pts: Domain age > 5 anni
+ 15 pts: Author noto/verificabile
+ 10 pts: No advertising presente
+ 10 pts: Fact-checking badges presente
+ 10 pts: Well-maintained (recent updates)
- 10 pts: Sensational headline
- 15 pts: Misinformation flags (fact-check.org)
- 25 pts: Noto predatore/spam domain

Score finale: 0-100 (50 è baseline neutrale)
```

---

## Formati di Citazione Supportati

### 1. Markdown (Default)

**Scopo**: Ideale per blog, documenti online, GitHub

**Sintassi Completa**:
```markdown
[Title](URL)
- Source: domain
- Author: name
- Published: date
- Accessed: date
- Context: "excerpt from content..."
```

**Esempio**:
```markdown
[Best Python Web Frameworks 2026](https://techblog.example.com/frameworks)
- Source: techblog.example.com
- Author: Jane Smith
- Published: February 20, 2026
- Accessed: February 28, 2026
- Context: "FastAPI has become the framework of choice for
  async web applications due to its high performance..."
```

### 2. HTML

**Scopo**: Embedding in siti web

```html
<cite>
  <a href="https://example.com/article">Article Title</a>
  <small>
    from <strong>example.com</strong>
    | by <em>John Doe</em>
    | accessed <time datetime="2026-02-28">Feb 28, 2026</time>
  </small>
</cite>
```

### 3. APA (American Psychological Association)

**Scopo**: Ricerca accademica, psicologia

**Formula**:
```
Author(s). (Year). Title of web page. Retrieved from URL
```

**Esempio**:
```
Smith, J. (2026). Best python web frameworks 2026.
Retrieved February 28, 2026, from
https://techblog.example.com/frameworks
```

**Variante con data di pubblicazione**:
```
Smith, J. (2026, February 20). Best python web frameworks 2026.
Retrieved February 28, 2026, from
https://techblog.example.com/frameworks
```

### 4. MLA (Modern Language Association)

**Scopo**: Lettere, scienze umane, lingue

**Formula**:
```
Author(s). "Title of Page." Title of Website, Date, URL.
Accessed Date.
```

**Esempio**:
```
Smith, Jane. "Best Python Web Frameworks 2026."
Tech Blog, 20 Feb. 2026, techblog.example.com/frameworks.
Accessed 28 Feb. 2026.
```

### 5. Chicago Manual of Style

**Scopo**: Libri, articoli storici, studi

**Note Style**:
```
Jane Smith, "Best Python Web Frameworks 2026,"
Tech Blog, February 20, 2026, https://techblog.example.com/frameworks.
```

**Bibliography Entry**:
```
Smith, Jane. "Best Python Web Frameworks 2026."
Tech Blog. February 20, 2026.
https://techblog.example.com/frameworks.
```

### 6. Plain Text

**Scopo**: Email, documenti semplici

```
Smith, J. Best Python Web Frameworks 2026.
https://techblog.example.com/frameworks
Accessed: Feb 28, 2026
```

---

## Gestione Citazioni nelle Sintesi

Quando SearchMuse sintetizza risultati, le citazioni sono integrate contextualmente:

### Inline Citations (Markdown)

```markdown
FastAPI has gained significant adoption in enterprise
environments[(source1)] due to its async support and high
performance[(source2)]. Unlike Django, which prioritizes
developer experience, FastAPI prioritizes[(source3)]
raw performance metrics.

---

[(source1)] Smith et al., 2026
[(source2)] Performance Benchmarks 2026
[(source3)] FastAPI Official Docs
```

### Footnote Style

```markdown
FastAPI has gained significant adoption in enterprise
environments¹ due to its async support and high performance².

¹ Smith, J., et al. "Framework Adoption 2026"
² "Python Web Framework Performance Benchmarks"
```

### Full Bibliography

```markdown
## Fonti Citate

1. [Best Python Web Frameworks 2026](https://example.com/1)
   - Author: Jane Smith
   - Accessed: Feb 28, 2026

2. [Framework Performance Benchmarks](https://example.com/2)
   - Source: BenchmarkSuite.io
   - Published: Feb 15, 2026

3. [FastAPI Documentation](https://fastapi.tiangolo.com)
   - Official documentation
   - Accessed: Feb 28, 2026
```

---

## Compliance e Verifica

SearchMuse effettua verifica automatica:

```python
citation_verification_checklist = {
    "url_valid": validates_url_format(),
    "url_accessible": test_http_head(),
    "content_exists": verify_content_unchanged(),
    "metadata_present": has_author_and_date(),
    "context_accurate": compare_extracted_vs_live(),
    "format_correct": adheres_to_citation_style(),
    "no_tracking_params": url_clean_of_utm(),
    "no_affiliate_links": url_clean_of_aff(),
}
```

Se uno o più check falliscono, la citazione è marcata con warning:

```markdown
⚠️ [Best Python Web Frameworks 2026](https://example.com/1)
   Status: Content may have changed
   Last verified: Feb 28, 2026
```

---

## Esempio End-to-End: Citazione di un Fatto

### Fatto trovato durante ricerca
```
"FastAPI reached 2M downloads in 2025"
```

### Citazione completa generata

**Markdown**:
```markdown
[FastAPI Reaches 2 Million Downloads in 2025](https://example.com/fastapi-downloads)
- Source: example.com
- Author: Alex Johnson
- Published: January 5, 2026
- Accessed: February 28, 2026
- Context: "FastAPI's package downloads surpassed 2 million
  monthly installs in December 2025, establishing it as a
  mainstream Python web framework..."
```

**APA**:
```
Johnson, A. (2026, January 5). FastAPI reaches 2 million
downloads in 2025. Retrieved February 28, 2026, from
https://example.com/fastapi-downloads
```

**MLA**:
```
Johnson, Alex. "FastAPI Reaches 2 Million Downloads in 2025."
Example, 5 Jan. 2026, example.com/fastapi-downloads.
Accessed 28 Feb. 2026.
```

---

## Best Practices per Utenti

Quando usi citazioni di SearchMuse:

1. **Sempre verificare l'URL**: Copia il link e aprilo indipendentemente
2. **Controllare il contesto**: Assicurati che il contesto estratto è rappresentativo
3. **Mantenere metadati**: Conserva author, date, URL anche se riformatti
4. **Aggiorna obsolete**: Se una citazione è molto vecchia, verifica che sia ancora accurata
5. **Rispetta i diritti d'autore**: Usa citazioni, non copie intere di contenuto

---

**Versione**: 1.0
**Ultimo aggiornamento**: 2026-02-28
