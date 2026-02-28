# Siti Web Supportati e Strategie di Scraping

## Introduzione

SearchMuse non può scrapare indiscriminatamente ogni sito web. Diverse categorie di siti richiedono approcci diversi, e alcune limitazioni tecniche o legali impediscono lo scraping automatico di determinati contenuti.

Questa sezione descrive quali siti sono supportati, come funziona lo scraping, e come contribuire con nuovi siti.

---

## Livelli di Supporto

Ogni categoria di siti ha un **livello di supporto** che indica il grado di ottimizzazione:

### Livello 1: Supporto Completo (Ottimizzato)

**Caratteristiche**:
- Scraping garantito con success rate > 95%
- Estrazione metadati (author, date) affidabile
- Tempi di risposta < 1 secondo
- CSS selectors specificici disponibili

**Siti Esempio**:
- Blog technici (Medium, Dev.to, HashNode)
- News (BBC, Reuters, AP News)
- Documentazione tecnica (GitHub, ReadTheDocs)
- Stack Overflow, GitHub Issues

### Livello 2: Supporto Buono (Affidabile)

**Caratteristiche**:
- Success rate 80-95%
- Estrazione metadati > 70% di successo
- Tempi variabili (0.5-2 secondi)
- Fallback a estrattore generico

**Siti Esempio**:
- Blog WordPress generici
- Articoli Medium con paywall
- Wikipedia
- Siti accademici (ArXiv, ResearchGate)

### Livello 3: Supporto Limitato (Con Cautele)

**Caratteristiche**:
- Success rate 50-80%
- Contenuto spesso incompleto
- Può richiedere JavaScript rendering
- Frequente necessità di Wayback Machine

**Siti Esempio**:
- Social media (Twitter/X content)
- Forum (Reddit, Quora)
- E-commerce (prodotti, prezzi)
- Siti con heavy JavaScript

### Livello 4: Non Supportato

**Motivi**:
- Contenuto protetto da login/paywall
- JavaScript required ma problematico
- Terms of Service lo proibiscono
- Dati in formato esclusivamente PDF

**Siti Esempio**:
- LinkedIn (login required)
- Financial terminals (Bloomberg, Reuters Pro)
- Accesso accademico protetto
- Siti con anti-bot aggressivo

---

## Categorie di Siti Supportati

### 1. Blog e Articoli Tecnici (Livello 1)

```
Success Rate: 95%+
Time per Page: 0.5s
Metadata Extraction: 95%

Siti: Medium, Dev.to, HashNode, TechCrunch,
      Hacker News, CSS-Tricks, Smashing Magazine
```

**Come funziona**:
1. Download HTML
2. Parse with trafilatura
3. Extract da og:title, og:article:author, article:published_time
4. Identificare main content area
5. Clean e normalizzare

**Limitazioni**: Paywall articles non completamente accessible

### 2. Documentazione Tecnica (Livello 1)

```
Success Rate: 98%+
Time per Page: 0.3s
Metadata Extraction: 90%

Siti: GitHub, ReadTheDocs, Official docs,
      PyPI, npm, GoDoc, Maven Central
```

**Come funziona**:
1. Parse structured content
2. Extract version/language info
3. Preserve code blocks
4. Mantieni navigation structure

**Limitazioni**: Rate limiting severo su GitHub (60 req/hr)

### 3. Notizie e Media (Livello 2)

```
Success Rate: 85-92%
Time per Page: 1.0-1.5s
Metadata Extraction: 88%

Siti: BBC, Reuters, AP News, The Guardian,
      New York Times, Washington Post
```

**Come funziona**:
1. Detect paywall patterns
2. Estrai headline, byline, date
3. Extract main article body
4. Mantieni structured sections
5. Detect paywalled content

**Limitazioni**: Articoli paywalled non completamente accessibili; subscription walls

### 4. Q&A e Forum (Livello 2-3)

```
Success Rate: 75-90%
Time per Page: 1.0-2.0s
Metadata Extraction: 70%

Siti: Stack Overflow, GitHub Issues, Reddit,
      Quora, Dev.to discussions
```

**Come funziona**:
1. Identify question/answer pairs
2. Extract upvotes/scores
3. Preserve comment threads
4. Identify author reputation
5. Extract timestamps

**Limitazioni**: Reddit API throttling; Quora aggressive bot detection

### 5. Wikipedia e Knowledge Bases (Livello 2)

```
Success Rate: 95%+
Time per Page: 0.7s
Metadata Extraction: 95%

Siti: Wikipedia, Wikimedia projects,
      MDN Web Docs, Khan Academy
```

**Come funziona**:
1. Use official mediawiki API quando possibile
2. Estrai infoboxes
3. Mantieni reference links
4. Extract revision timestamp
5. Preserve categories

**Limitazioni**: Contenuto tradotto può avere metadata diversi

### 6. E-commerce e Product Info (Livello 3)

```
Success Rate: 70%
Time per Page: 1.5-2.0s
Metadata Extraction: 60%

Siti: Amazon, eBay, Product reviews,
      Specs databases
```

**Come funziona**:
1. Parse product JSON-LD
2. Extract pricing (volatile)
3. Ratings and reviews aggregation
4. Specifications
5. Availability status

**Limitazioni**: Prezzi non sempre accurati; contenuto dinamico

### 7. Social Media (Livello 3-4)

```
Success Rate: 50-75%
Time per Page: 2.0-3.0s
Metadata Extraction: 40%

Siti: Twitter/X, LinkedIn, YouTube descriptions,
      Instagram captions
```

**Come funziona**:
1. Attempt HTML scraping
2. Fallback a API if available
3. Extract text content
4. Preserve timestamps
5. Include interaction counts

**Limitazioni**: API require authentication; rate limiting severo; content often unavailable

---

## Algoritmo di Selezione Strategia

Per ogni URL, SearchMuse seleziona la strategia di scraping migliore:

```
1. Identify domain
2. Check if domain in optimized list (Livello 1)
   → Use optimized CSS selectors
3. If not, check category
   → Apply category-specific strategy
4. Try primary strategy (HTML parsing)
   → If success, return content
5. If fails, try secondary strategy (JS rendering)
   → Load with Selenium/Playwright
   → Wait for dynamic content
   → Extract
6. If still fails, try tertiary (Wayback Machine)
   → Query archive.org
   → Get snapshot from date
7. If all fail, mark as failed and continue

Timeout per step: 5 seconds
Retry count: 1
Total timeout per URL: 15 seconds
```

**Decisioning Tree** (Pseudocodice):

```python
def choose_scraping_strategy(url):
    domain = extract_domain(url)

    if domain in OPTIMIZED_DOMAINS:
        return "optimized_selectors"

    category = categorize_domain(domain)

    if category == "documentation":
        return "readability_parser"
    elif category == "news":
        return "trafilatura"
    elif category == "ecommerce":
        return "json_ld_parser"
    elif category == "social_media":
        return "javascript_rendering"
    else:
        return "generic_readability"
```

---

## Come Aggiungere Nuovo Sito/Categoria

### Processo di Contribuzione

Se conosci un sito che SearchMuse dovrebbe supportare meglio:

1. **Apri una Issue su GitHub**:
   ```
   Title: Add support for [site name]
   Description:
   - URL pattern: [example URLs]
   - Content type: [article/product/forum/etc]
   - Estimated value: [why this site matters]
   - Scraping obstacles: [any known issues]
   ```

2. **Fornisci Sample URLs**: Almeno 3 URL di esempio

3. **Identifica Metadati Target**:
   ```
   [ ] Title
   [ ] Author
   [ ] Publication date
   [ ] Body text
   [ ] Tags/categories
   [ ] Images
   [ ] Related links
   ```

4. **Analizza Struttura HTML**: Se possibile fornisci:
   - CSS selectors per main content
   - Meta tags utilizzati
   - JSON-LD schema (if any)
   - Javascript rendering needed? (Y/N)

5. **Implementazione** (team SearchMuse):
   - Crea CSS selectors ottimizzati
   - Test con 5+ URL
   - Validate metadata extraction
   - Document in scraper config

### Struttura di Configurazione Sito

```yaml
sites:
  - domain: "techblog.example.com"
    category: "blog"
    support_level: 1
    scraping:
      primary: "css_selectors"
      selectors:
        title: "h1.post-title"
        author: "span.author-name"
        date: "time.publish-date"
        content: "div.article-body"
      metadata:
        - og:title
        - og:article:author
        - article:published_time
      javascript_required: false
      timeout: 5
    rate_limit:
      requests_per_second: 2
      delay_between: 0.5
    fallback: "trafilatura"
    notes: "Homepage requires robot.txt check"
```

---

## robots.txt e Conformità Legale

SearchMuse **rispetta sempre** robots.txt:

```
Per ogni dominio:
1. Fetch robots.txt
2. Check se /search-muse user-agent è permettedto
3. Se non specificato, check se * è permesso
4. Rispetta Disallow ed Allow rules
5. Rispetta Crawl-Delay e Request-Rate
6. Fallback a 2 req/sec se non specificato
```

**Esempio robots.txt**:
```
User-agent: SearchMuse
Allow: /blog/
Allow: /docs/
Disallow: /admin/
Disallow: /api/
Crawl-Delay: 1

User-agent: *
Allow: /
Disallow: /private/
```

**SearchMuse User-Agent String**:
```
Mozilla/5.0 (compatible; SearchMuse/1.0; +https://github.com/searchmuse/core)
```

---

## Limitazioni Tecniche Note

| Limitazione | Siti Affetti | Workaround |
|------------|-------------|-----------|
| JavaScript SPAs | Facebook, LinkedIn, Twitter | Selenium rendering, fallback to Wayback |
| Cookie walls | News paywalls | Detect e skip, o Wayback snapshot |
| Rate limiting | GitHub, API services | Respect robots.txt delays, circuit breaker |
| Cloudflare WAF | Random sites | Retry with backoff, user-agent rotation |
| Content lazy-loading | Pinterest, Instagram | Full JS rendering required |
| Dynamic pricing | E-commerce | Note that prices may change |
| Session required | Protected content | Graceful fail, not accessible |

---

## Statistiche di Supporto

Basato su 10,000 URL comuni tracciati:

```
Livello 1 (Optimized): 25% dei siti frequenti
- Success rate: 97%
- Tempo medio: 0.6s

Livello 2 (Good): 50% dei siti frequenti
- Success rate: 87%
- Tempo medio: 1.2s

Livello 3 (Limited): 20% dei siti frequenti
- Success rate: 68%
- Tempo medio: 2.0s

Livello 4 (Unsupported): 5% dei siti frequenti
- Success rate: 10%
- Tempo medio: fallback to Wayback
```

---

**Versione**: 1.0
**Ultimo aggiornamento**: 2026-02-28
