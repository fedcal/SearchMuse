# Riferimento Configurazione

SearchMuse usa file YAML per la configurazione. Questo documento descrive tutti i parametri disponibili e come configurarli.

## Posizioni dei File di Configurazione

SearchMuse cerca i file di configurazione in questo ordine (primo trovato vince):

1. `~/.searchmuse/config.yaml` - Configurazione utente globale
2. `/etc/searchmuse/config.yaml` - Configurazione di sistema (Linux)
3. `./searchmuse.yaml` - Configurazione locale nella directory corrente
4. Variabili di ambiente (prefisso `SEARCHMUSE_`)

## Struttura Base del File di Configurazione

```yaml
# searchmuse.yaml

# Configurazione Ollama
ollama:
  host: localhost
  port: 11434
  model: mistral
  timeout: 30
  retry_attempts: 3

# Configurazione Ricerca
search:
  engine: duckduckgo
  max_results_per_iteration: 5
  language: it
  safe_search: true
  timeout: 10

# Configurazione Web Scraper
scraper:
  type: playwright
  headless: true
  timeout: 10000
  disable_images: true
  disable_css: false
  proxy: null

# Configurazione Repository
repository:
  type: sqlite
  database_path: ~/.searchmuse/sessions.db
  max_session_age_days: 90

# Configurazione Logging
logging:
  level: INFO
  format: json
  output: console

# Configurazione Ricerca
research:
  max_iterations: 3
  parallel_searches: false
  cache_results: true
  cache_ttl_hours: 24
```

## Parametri Dettagliati

### Sezione ollama

Configura la comunicazione con Ollama.

```yaml
ollama:
  host: localhost
  # Host del server Ollama
  # Default: localhost
  # Può essere: localhost, 127.0.0.1, IP esterno, hostname

  port: 11434
  # Porta del server Ollama
  # Default: 11434
  # Range: 1-65535

  model: mistral
  # Modello da usare
  # Opzioni comuni: mistral, neural-chat, llama2, openchat
  # Default: mistral
  # Note: Deve essere già scaricato da Ollama

  timeout: 30
  # Timeout delle richieste in secondi
  # Default: 30
  # Min: 1, Max: 300

  retry_attempts: 3
  # Numero di tentativi in caso di errore
  # Default: 3
  # Min: 1, Max: 10

  temperature: 0.7
  # Controllo della creatività della risposta (0.0-1.0)
  # 0.0 = deterministico, 1.0 = creativo
  # Default: 0.7

  top_p: 0.9
  # Nucleus sampling parameter
  # Default: 0.9
  # Range: 0.0-1.0
```

### Sezione search

Configura il motore di ricerca.

```yaml
search:
  engine: duckduckgo
  # Motore di ricerca da usare
  # Opzioni: duckduckgo, google, bing
  # Default: duckduckgo
  # Note: google e bing richiedono API keys

  max_results_per_iteration: 5
  # Numero di risultati per iterazione
  # Default: 5
  # Min: 1, Max: 20
  # Note: Più risultati = ricerca più lenta ma più completa

  language: it
  # Lingua dei risultati (codice ISO 639-1)
  # Opzioni: it, en, es, fr, de, etc.
  # Default: it

  safe_search: true
  # Abilitare la ricerca sicura
  # Default: true
  # Note: Filtra contenuti espliciti

  timeout: 10
  # Timeout della ricerca in secondi
  # Default: 10
  # Min: 1, Max: 60

  rate_limit_delay: 0.5
  # Ritardo tra richieste successive (secondi)
  # Default: 0.5
  # Min: 0, Max: 5
  # Note: Evita il rate limiting del motore di ricerca
```

### Sezione scraper

Configura il web scraper.

```yaml
scraper:
  type: playwright
  # Tipo di scraper
  # Opzioni: playwright, httpx
  # Default: playwright
  # Note: playwright supporta JavaScript, httpx è più veloce

  headless: true
  # Eseguire il browser in headless mode
  # Default: true
  # Note: false abilita il browser visibile per debugging

  timeout: 10000
  # Timeout di navigazione in millisecondi
  # Default: 10000
  # Min: 1000, Max: 60000

  disable_images: true
  # Non scaricare le immagini
  # Default: true
  # Note: Velocizza il caricamento

  disable_css: false
  # Non scaricare i CSS
  # Default: false
  # Note: Utile solo se non serve rendering CSS

  proxy: null
  # URL proxy da usare
  # Default: null (nessun proxy)
  # Esempio: "http://proxy.azienda.it:8080"

  user_agent: null
  # User-Agent personalizzato
  # Default: null (usa quello di default del browser)
  # Esempio: "Mozilla/5.0 (Custom) ..."

  javascript_wait_ms: 2000
  # Tempo di attesa dopo rendering JavaScript
  # Default: 2000
  # Min: 0, Max: 10000
```

### Sezione repository

Configura la persistenza.

```yaml
repository:
  type: sqlite
  # Tipo di repository
  # Opzioni: sqlite, postgres
  # Default: sqlite
  # Note: postgres richiede configurazione aggiuntiva

  database_path: ~/.searchmuse/sessions.db
  # Percorso del database SQLite
  # Default: ~/.searchmuse/sessions.db
  # Note: Espandi ~ alla home directory

  max_session_age_days: 90
  # Giorni prima di eliminare sessioni vecchie
  # Default: 90
  # Min: 1, Max: 3650
  # Note: 0 = nessuna eliminazione automatica

  connection_pool_size: 5
  # Dimensione del pool di connessioni
  # Default: 5
  # Min: 1, Max: 20
  # Note: Solo per postgres
```

### Sezione logging

Configura il logging.

```yaml
logging:
  level: INFO
  # Livello di log
  # Opzioni: DEBUG, INFO, WARNING, ERROR, CRITICAL
  # Default: INFO

  format: json
  # Formato dei log
  # Opzioni: json, text
  # Default: json
  # Note: json è più parseable dai sistemi di monitoring

  output: console
  # Output dei log
  # Opzioni: console, file, syslog
  # Default: console

  file_path: ~/.searchmuse/searchmuse.log
  # Percorso del file log (se output=file)
  # Default: ~/.searchmuse/searchmuse.log

  max_file_size_mb: 100
  # Dimensione massima del file log
  # Default: 100
  # Min: 1, Max: 1000

  backup_count: 5
  # Numero di file log di backup da mantenere
  # Default: 5
  # Min: 1, Max: 20

  include_timestamps: true
  # Includere timestamp nei log
  # Default: true

  include_caller: true
  # Includere file e linea del caller nei log
  # Default: true
```

### Sezione research

Configura i parametri di ricerca.

```yaml
research:
  max_iterations: 3
  # Numero massimo di iterazioni per ricerca
  # Default: 3
  # Min: 1, Max: 10
  # Note: Più iterazioni = ricerca più accurata ma più lenta

  parallel_searches: false
  # Eseguire ricerche in parallelo (sperimentale)
  # Default: false
  # Note: Incrementa consumo di risorse

  cache_results: true
  # Abilitare il caching dei risultati
  # Default: true
  # Note: Velocizza ricerche ripetute

  cache_ttl_hours: 24
  # Tempo di vita del cache in ore
  # Default: 24
  # Min: 1, Max: 2160 (90 giorni)

  min_citations_required: 2
  # Numero minimo di citazioni richieste
  # Default: 2
  # Min: 1, Max: 20

  chunk_size_chars: 2000
  # Dimensione dei chunk per l'LLM
  # Default: 2000
  # Min: 500, Max: 10000
  # Note: Testo più lungo = contesto migliore ma latenza maggiore
```

## Variabili di Ambiente

Qualsiasi parametro YAML può essere sovrascritto con variabili di ambiente usando il formato `SEARCHMUSE_<SEZIONE>_<PARAMETRO>`:

```bash
# Esempi di variabili di ambiente

# Ollama
export SEARCHMUSE_OLLAMA_HOST=192.168.1.100
export SEARCHMUSE_OLLAMA_MODEL=neural-chat
export SEARCHMUSE_OLLAMA_TIMEOUT=60

# Search
export SEARCHMUSE_SEARCH_ENGINE=google
export SEARCHMUSE_SEARCH_LANGUAGE=en

# Research
export SEARCHMUSE_RESEARCH_MAX_ITERATIONS=5
export SEARCHMUSE_RESEARCH_CACHE_TTL_HOURS=48

# Repository
export SEARCHMUSE_REPOSITORY_DATABASE_PATH=/data/sessions.db
```

Le variabili di ambiente hanno priorità sulla configurazione YAML.

## Configurazioni di Esempio

### Configurazione Minimalista

```yaml
# Per uso locale veloce
ollama:
  model: mistral

search:
  max_results_per_iteration: 3

research:
  max_iterations: 2
```

### Configurazione Produzione

```yaml
ollama:
  host: ollama.service.internal
  port: 11434
  model: mistral
  timeout: 60
  retry_attempts: 5
  temperature: 0.5

search:
  engine: duckduckgo
  max_results_per_iteration: 10
  safe_search: true
  timeout: 20
  rate_limit_delay: 1.0

scraper:
  type: playwright
  headless: true
  timeout: 15000
  disable_images: true

repository:
  type: sqlite
  database_path: /var/lib/searchmuse/sessions.db
  max_session_age_days: 180

logging:
  level: INFO
  format: json
  output: file
  file_path: /var/log/searchmuse/app.log
  max_file_size_mb: 500
  backup_count: 10

research:
  max_iterations: 5
  cache_results: true
  cache_ttl_hours: 48
  min_citations_required: 3
```

### Configurazione Development

```yaml
ollama:
  host: localhost
  model: mistral
  timeout: 30
  temperature: 0.8

search:
  engine: duckduckgo
  max_results_per_iteration: 5
  timeout: 10

scraper:
  type: playwright
  headless: true
  timeout: 10000
  disable_images: false

repository:
  type: sqlite
  database_path: ./dev_sessions.db

logging:
  level: DEBUG
  format: text
  output: console
  include_caller: true

research:
  max_iterations: 3
  cache_results: true
  cache_ttl_hours: 1
```

## Validazione della Configurazione

Verificare la configurazione caricata:

```bash
# Mostra la configurazione attuale
searchmuse config show

# Valida la configurazione
searchmuse config validate

# Mostra i defaults
searchmuse config defaults
```

## Risoluzione dei Problemi

### Ollama non raggiungibile

```bash
# Verificare che Ollama sia in esecuzione
curl http://localhost:11434/api/tags

# Se non funziona, controllare l'host/porta in config.yaml
# Oppure usare variabili di ambiente:
export SEARCHMUSE_OLLAMA_HOST=192.168.1.100
export SEARCHMUSE_OLLAMA_PORT=11434
```

### Database lock

```yaml
# Se ricevi errori di database lock, ridurre il numero di iterazioni
research:
  max_iterations: 2
```

### Timeout troppo aggressivo

```yaml
# Se ricevi timeout frequenti, aumentare i timeout
ollama:
  timeout: 60

search:
  timeout: 20

scraper:
  timeout: 20000
```

---

**Versione**: 1.0
**Ultimo Aggiornamento**: Febbraio 2026
**Stato**: Stabile
