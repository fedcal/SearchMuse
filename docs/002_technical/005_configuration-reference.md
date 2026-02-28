# SearchMuse Configuration Reference

Complete guide to configuring SearchMuse behavior through YAML configuration files and environment variables.

## Configuration Loading

SearchMuse loads configuration in the following precedence order (highest to lowest):

1. **Environment variables** (SEARCHMUSE_* prefix)
2. **Custom YAML file** (--config parameter or config/ directory)
3. **Default YAML file** (config/default.yaml)

This allows environment variables to override file settings, enabling containerized deployments.

## Default Configuration

**File:** `config/default.yaml`

Contains sensible defaults for all settings. Never modify this file; create a custom config instead.

## Configuration Structure

All configuration is organized into sections:

```yaml
search:
  # Search engine settings
llm:
  # Language model settings
scraper:
  # Web scraping settings
extraction:
  # Content extraction settings
repository:
  # Data storage settings
rendering:
  # Output formatting settings
timeouts:
  # Operation timeouts
limits:
  # Resource limits
logging:
  # Logging configuration
```

## Search Configuration

### Section: `search`

```yaml
search:
  # Engine to use: 'duckduckgo' | 'google' | 'bing'
  engine: duckduckgo

  # Results per search query
  results_per_query: 10

  # Maximum results across all iterations
  max_total_results: 100

  # Relevance threshold for filtering (0.0-1.0)
  relevance_threshold: 0.6

  # Language code for search results
  language: en

  # Respect robots.txt
  respect_robots_txt: true

  # Rate limit: milliseconds between requests to same domain
  rate_limit_ms: 1000
```

**Environment Variables:**
- `SEARCHMUSE_SEARCH_ENGINE` = duckduckgo
- `SEARCHMUSE_SEARCH_RESULTS_PER_QUERY` = 10
- `SEARCHMUSE_SEARCH_RELEVANCE_THRESHOLD` = 0.6

---

## LLM Configuration

### Section: `llm`

```yaml
llm:
  # Provider: 'ollama' | 'openai' | 'anthropic'
  provider: ollama

  # Model name/identifier
  model: mistral

  # Ollama configuration (if provider: ollama)
  ollama:
    base_url: http://localhost:11434
    timeout_seconds: 60

  # Temperature for generation (0.0-2.0)
  # Lower = more deterministic, higher = more creative
  temperature: 0.7

  # Maximum tokens for strategy generation
  max_tokens_strategy: 100

  # Maximum tokens for synthesis
  max_tokens_synthesis: 1000

  # System prompt for strategy generation
  strategy_prompt: >
    You are a research assistant helping refine search strategies.
    Based on the research query and previous results, suggest specific
    search terms to find more relevant sources. Keep suggestions concise.

  # System prompt for synthesis
  synthesis_prompt: >
    You are a research synthesizer. Based on the provided sources and
    evidence, create a comprehensive answer to the research question.
    Include citations from sources. Format in markdown.
```

**Environment Variables:**
- `SEARCHMUSE_LLM_PROVIDER` = ollama
- `SEARCHMUSE_LLM_MODEL` = mistral
- `SEARCHMUSE_LLM_TEMPERATURE` = 0.7
- `SEARCHMUSE_OLLAMA_BASE_URL` = http://localhost:11434

**Ollama Model Selection:**
- `mistral` (7B) - Fast, good quality, recommended for CPU
- `neural-chat` (7B) - Conversation-optimized
- `llama2` (7B/13B) - General purpose
- `mixtral` (8x7B) - High quality, requires more RAM

---

## Scraper Configuration

### Section: `scraper`

```yaml
scraper:
  # Default scraper: 'httpx' | 'playwright'
  default: httpx

  # Playwright browser for JS-heavy sites: 'chromium' | 'firefox' | 'webkit'
  browser: chromium

  # Run browser headless (no GUI)
  headless: true

  # Custom User-Agent header
  user_agent: >
    Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36
    (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36

  # Request timeout per URL (seconds)
  timeout_seconds: 10

  # JavaScript rendering timeout (seconds)
  javascript_timeout_seconds: 30

  # Maximum redirects to follow
  max_redirects: 5

  # Enable cookies
  enable_cookies: true

  # Accept gzip compression
  accept_encoding: gzip, deflate

  # Retry failed requests
  retry_attempts: 2
  retry_backoff_factor: 1.5
```

**Environment Variables:**
- `SEARCHMUSE_SCRAPER_DEFAULT` = httpx
- `SEARCHMUSE_SCRAPER_TIMEOUT_SECONDS` = 10
- `SEARCHMUSE_SCRAPER_BROWSER` = chromium

---

## Extraction Configuration

### Section: `extraction`

```yaml
extraction:
  # Extractor: 'trafilatura' | 'readability'
  engine: trafilatura

  # Include tables in extraction
  include_tables: true

  # Include code blocks in extraction
  include_code: true

  # Include images metadata
  include_images: false

  # Maximum content length (chars)
  max_length: 100000

  # Minimum content length to consider article
  min_length: 500

  # Include comments
  include_comments: false

  # Language detection
  detect_language: true
```

**Environment Variables:**
- `SEARCHMUSE_EXTRACTION_ENGINE` = trafilatura
- `SEARCHMUSE_EXTRACTION_MAX_LENGTH` = 100000

---

## Repository Configuration

### Section: `repository`

```yaml
repository:
  # Storage type: 'sqlite' | 'postgres'
  type: sqlite

  # SQLite configuration
  sqlite:
    # Database file path
    path: ./data/searchmuse.db

    # Enable WAL (Write-Ahead Logging) for better concurrency
    journal_mode: wal

    # Synchronous mode: 0 (FULL), 1 (NORMAL), 2 (SYNC)
    synchronous: 1

  # PostgreSQL configuration (if type: postgres)
  postgres:
    host: localhost
    port: 5432
    database: searchmuse
    user: searchmuse
    password: ${DB_PASSWORD}  # Load from env var

  # Automatic cleanup of old sources (days)
  cleanup_older_than_days: 90

  # Maximum stored sources per query
  max_sources_per_query: 1000
```

**Environment Variables:**
- `SEARCHMUSE_REPOSITORY_TYPE` = sqlite
- `SEARCHMUSE_REPOSITORY_SQLITE_PATH` = ./data/searchmuse.db
- `SEARCHMUSE_REPOSITORY_POSTGRES_HOST` = localhost
- `DB_PASSWORD` = (for postgres password)

---

## Rendering Configuration

### Section: `rendering`

```yaml
rendering:
  # Output format: 'markdown' | 'html' | 'json'
  format: markdown

  # Markdown settings
  markdown:
    # Include table of contents
    include_toc: true

    # Include execution time
    include_metrics: true

    # Citation format: 'apa' | 'chicago' | 'mla'
    citation_format: apa

    # Maximum sources to display
    max_sources: 50

  # HTML settings
  html:
    # Include CSS styling
    include_css: true

    # Dark mode support
    dark_mode: false

    # Mobile responsive
    responsive: true

  # JSON settings
  json:
    # Pretty-print JSON
    indent: 2

    # Include schema
    include_schema: false
```

**Environment Variables:**
- `SEARCHMUSE_RENDERING_FORMAT` = markdown
- `SEARCHMUSE_RENDERING_MARKDOWN_CITATION_FORMAT` = apa

---

## Timeout Configuration

### Section: `timeouts`

```yaml
timeouts:
  # Total research execution timeout (seconds)
  total_research: 300

  # Per-iteration timeout (seconds)
  per_iteration: 60

  # Per-search timeout (seconds)
  search: 15

  # Per-scrape timeout (seconds)
  scrape: 10

  # Content extraction timeout (seconds)
  extraction: 10

  # LLM request timeout (seconds)
  llm: 60

  # Database operation timeout (seconds)
  database: 5
```

**Environment Variables:**
- `SEARCHMUSE_TIMEOUTS_TOTAL_RESEARCH` = 300
- `SEARCHMUSE_TIMEOUTS_SCRAPE` = 10

---

## Limits Configuration

### Section: `limits`

```yaml
limits:
  # Maximum iterations per research session
  max_iterations: 5

  # Minimum iterations before allowing stop
  min_iterations: 1

  # Maximum query length (characters)
  max_query_length: 1000

  # Maximum sources per iteration
  max_sources_per_iteration: 20

  # Maximum content block size (characters)
  max_block_size: 10000

  # Maximum concurrent scraping operations
  max_concurrent_scrapes: 5

  # Maximum concurrent extractions
  max_concurrent_extractions: 3
```

**Environment Variables:**
- `SEARCHMUSE_LIMITS_MAX_ITERATIONS` = 5
- `SEARCHMUSE_LIMITS_MAX_QUERY_LENGTH` = 1000

---

## Logging Configuration

### Section: `logging`

```yaml
logging:
  # Log level: DEBUG | INFO | WARNING | ERROR | CRITICAL
  level: INFO

  # Log file path (optional)
  file: ./logs/searchmuse.log

  # Maximum log file size (MB) before rotation
  max_file_size_mb: 50

  # Number of backup log files to keep
  backup_count: 5

  # Log format
  format: >
    %(asctime)s - %(name)s - %(levelname)s - %(message)s

  # Log to console
  console: true

  # Modules to debug (more verbose)
  debug_modules:
    # - searchmuse.adapters.ollama_llm
    # - searchmuse.adapters.httpx_scraper
```

**Environment Variables:**
- `SEARCHMUSE_LOGGING_LEVEL` = INFO
- `SEARCHMUSE_LOGGING_FILE` = ./logs/searchmuse.log

---

## Example Configurations

### Minimal Configuration

For basic usage with defaults:

```yaml
# config/minimal.yaml
llm:
  provider: ollama
  model: mistral

search:
  engine: duckduckgo
```

### High-Performance Configuration

Optimized for speed with more concurrent operations:

```yaml
# config/performance.yaml
limits:
  max_concurrent_scrapes: 10
  max_concurrent_extractions: 5

timeouts:
  total_research: 180
  per_iteration: 40

search:
  results_per_query: 20
  max_total_results: 50

llm:
  temperature: 0.5  # More deterministic
```

### Privacy-Focused Configuration

Minimal external dependencies:

```yaml
# config/privacy.yaml
search:
  engine: duckduckgo
  respect_robots_txt: true
  rate_limit_ms: 2000

scraper:
  default: httpx
  user_agent: Mozilla/5.0 SearchMuse Research Bot

repository:
  type: sqlite
  sqlite:
    path: ./local_data/searchmuse.db
  cleanup_older_than_days: 30
```

### Production Configuration

Suitable for server deployments:

```yaml
# config/production.yaml
repository:
  type: postgres
  postgres:
    host: ${DB_HOST}
    port: ${DB_PORT}
    database: searchmuse_prod
    user: ${DB_USER}
    password: ${DB_PASSWORD}

logging:
  level: WARNING
  file: /var/log/searchmuse/research.log
  backup_count: 10

limits:
  max_iterations: 3
  max_sources_per_iteration: 10

search:
  rate_limit_ms: 2000
```

## Loading Custom Configuration

### Via Command Line

```bash
searchmuse --config config/custom.yaml research "quantum computing"
```

### Via Environment Variable

```bash
export SEARCHMUSE_CONFIG=config/custom.yaml
searchmuse research "quantum computing"
```

### Programmatically

```python
from searchmuse.infrastructure.config import ConfigLoader

config = ConfigLoader.from_file("config/custom.yaml")
# Use config for initialization
```

## Validation

SearchMuse validates configuration on startup:

- All paths must be absolute or relative to project root
- Timeouts must be positive integers
- Limits must be positive integers
- Temperatures must be 0.0-2.0
- Relevance threshold must be 0.0-1.0

Invalid configuration raises `ConfigurationError` with details.

## Related Documentation

- [Development Setup](006_development-setup.md) - Initial configuration
- [Deployment Guide](008_deployment.md) - Production configuration
- [Components Guide](002_components.md) - Component-specific config

---

Last updated: 2026-02-28
