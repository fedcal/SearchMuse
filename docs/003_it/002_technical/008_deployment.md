# Distribuzione e Produzione

Questa guida spiega come distribuire SearchMuse in ambienti di produzione.

## Requisiti Hardware

### Configurazione Minima

- **CPU**: 2 core
- **RAM**: 2 GB
- **Spazio disco**: 10 GB (per database + log)
- **Rete**: Connessione internet stabile

### Configurazione Consigliata (Produzione)

- **CPU**: 4+ core
- **RAM**: 8+ GB (4 GB per Ollama, 2 GB per SearchMuse, 2 GB buffer)
- **Spazio disco**: 50+ GB (per cache, database, log)
- **Rete**: Banda larga, bassa latenza

## Deployment con Docker

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Installare dipendenze di sistema
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Installare Playwright browsers (opzionale se non usando Playwright)
RUN apt-get update && apt-get install -y \
    libgconf-2-4 \
    libx11-6 \
    libxext6 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

# Copiare il codice
COPY . /app

# Installare Python dipendenze
RUN pip install --no-cache-dir -e .

# Creare directory per database e logs
RUN mkdir -p /var/lib/searchmuse /var/log/searchmuse

# Esporre porta (opzionale per servizio HTTP)
EXPOSE 8000

# Variabili di ambiente
ENV SEARCHMUSE_REPOSITORY_DATABASE_PATH=/var/lib/searchmuse/sessions.db
ENV SEARCHMUSE_LOGGING_FILE_PATH=/var/log/searchmuse/searchmuse.log

# Comando di avvio
CMD ["searchmuse", "search", "--help"]
```

### Docker Compose

Deployment completo con SearchMuse e Ollama:

```yaml
version: '3.8'

services:
  ollama:
    image: ollama/ollama:latest
    container_name: searchmuse-ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama-data:/root/.ollama
    environment:
      - OLLAMA_HOST=0.0.0.0:11434
    command: serve
    networks:
      - searchmuse-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11434/api/tags"]
      interval: 30s
      timeout: 10s
      retries: 3

  searchmuse:
    build: .
    container_name: searchmuse-app
    depends_on:
      ollama:
        condition: service_healthy
    volumes:
      - searchmuse-data:/var/lib/searchmuse
      - searchmuse-logs:/var/log/searchmuse
      - ./config.yaml:/etc/searchmuse/config.yaml:ro
    environment:
      - SEARCHMUSE_OLLAMA_HOST=ollama
      - SEARCHMUSE_OLLAMA_PORT=11434
      - SEARCHMUSE_OLLAMA_MODEL=mistral
      - SEARCHMUSE_REPOSITORY_DATABASE_PATH=/var/lib/searchmuse/sessions.db
      - SEARCHMUSE_LOGGING_FILE_PATH=/var/log/searchmuse/searchmuse.log
    networks:
      - searchmuse-network
    restart: unless-stopped

volumes:
  ollama-data:
  searchmuse-data:
  searchmuse-logs:

networks:
  searchmuse-network:
    driver: bridge
```

### Avvio con Docker Compose

```bash
# Scaricare immagini e avviare
docker-compose up -d

# Verificare lo stato
docker-compose ps

# Visualizzare i log
docker-compose logs -f searchmuse

# Eseguire comando
docker-compose exec searchmuse searchmuse search "query"

# Fermare i servizi
docker-compose down
```

## Deployment con Systemd (Linux)

### 1. Installare l'Applicazione

```bash
# Clonare il repository in /opt
sudo git clone https://github.com/federicocalo/WebScraping.git /opt/searchmuse

# Installare dipendenze
cd /opt/searchmuse
sudo pip install -e .

# Creare utente dedicato
sudo useradd -r -s /bin/bash searchmuse

# Impostare permessi
sudo chown -R searchmuse:searchmuse /opt/searchmuse
sudo mkdir -p /var/lib/searchmuse /var/log/searchmuse
sudo chown searchmuse:searchmuse /var/lib/searchmuse /var/log/searchmuse
```

### 2. Creare File di Servizio

Creare `/etc/systemd/system/searchmuse.service`:

```ini
[Unit]
Description=SearchMuse Web Research Assistant
After=network.target ollama.service
Wants=ollama.service

[Service]
Type=simple
User=searchmuse
Group=searchmuse
WorkingDirectory=/opt/searchmuse

Environment="SEARCHMUSE_REPOSITORY_DATABASE_PATH=/var/lib/searchmuse/sessions.db"
Environment="SEARCHMUSE_LOGGING_FILE_PATH=/var/log/searchmuse/searchmuse.log"
Environment="SEARCHMUSE_OLLAMA_HOST=localhost"
Environment="SEARCHMUSE_OLLAMA_PORT=11434"

# Se usando CLI interattiva, commentare ExecStart e usare ExecStartPre per setup
ExecStart=/opt/searchmuse/venv/bin/python -m searchmuse.cli

# Restart policy
Restart=on-failure
RestartSec=10

# Security
NoNewPrivileges=true
PrivateTmp=true

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=searchmuse

[Install]
WantedBy=multi-user.target
```

### 3. Creare File di Servizio per Ollama

Creare `/etc/systemd/system/ollama.service`:

```ini
[Unit]
Description=Ollama LLM Service
After=network.target

[Service]
Type=simple
User=ollama
Group=ollama
ExecStart=/usr/bin/ollama serve
Restart=on-failure
RestartSec=5

Environment="OLLAMA_MODELS=/var/lib/ollama/models"
Environment="OLLAMA_HOST=0.0.0.0:11434"

StandardOutput=journal
StandardError=journal
SyslogIdentifier=ollama

[Install]
WantedBy=multi-user.target
```

### 4. Gestione dei Servizi

```bash
# Ricaricare la configurazione systemd
sudo systemctl daemon-reload

# Abilitare al boot
sudo systemctl enable ollama.service
sudo systemctl enable searchmuse.service

# Avviare i servizi
sudo systemctl start ollama.service
sudo systemctl start searchmuse.service

# Controllare lo stato
sudo systemctl status ollama.service
sudo systemctl status searchmuse.service

# Visualizzare i log
sudo journalctl -u searchmuse.service -f
sudo journalctl -u ollama.service -f

# Fermare i servizi
sudo systemctl stop searchmuse.service
sudo systemctl stop ollama.service
```

## Configurazione di Produzione

### Variabili di Ambiente

```bash
# .env per production
SEARCHMUSE_OLLAMA_HOST=ollama.internal
SEARCHMUSE_OLLAMA_PORT=11434
SEARCHMUSE_OLLAMA_MODEL=mistral
SEARCHMUSE_OLLAMA_TIMEOUT=60

SEARCHMUSE_SEARCH_ENGINE=duckduckgo
SEARCHMUSE_SEARCH_MAX_RESULTS_PER_ITERATION=10

SEARCHMUSE_SCRAPER_TIMEOUT=15000
SEARCHMUSE_SCRAPER_HEADLESS=true
SEARCHMUSE_SCRAPER_DISABLE_IMAGES=true

SEARCHMUSE_REPOSITORY_TYPE=sqlite
SEARCHMUSE_REPOSITORY_DATABASE_PATH=/var/lib/searchmuse/sessions.db
SEARCHMUSE_REPOSITORY_MAX_SESSION_AGE_DAYS=180

SEARCHMUSE_LOGGING_LEVEL=INFO
SEARCHMUSE_LOGGING_FORMAT=json
SEARCHMUSE_LOGGING_OUTPUT=file
SEARCHMUSE_LOGGING_FILE_PATH=/var/log/searchmuse/app.log

SEARCHMUSE_RESEARCH_MAX_ITERATIONS=5
SEARCHMUSE_RESEARCH_CACHE_TTL_HOURS=48
```

### YAML Configuration

`/etc/searchmuse/config.yaml`:

```yaml
ollama:
  host: ollama.internal
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

## Monitoraggio

### Logging

SearchMuse produce log in formato JSON per facilità di parsing:

```bash
# Visualizzare i log in tempo reale
tail -f /var/log/searchmuse/searchmuse.log

# Parsare i log JSON
cat /var/log/searchmuse/searchmuse.log | jq '.level, .message'

# Filtrar per errori
cat /var/log/searchmuse/searchmuse.log | jq 'select(.level=="ERROR")'
```

### Health Check

```bash
# Verificare che Ollama sia raggiungibile
curl -f http://localhost:11434/api/tags

# Verificare il database
sqlite3 /var/lib/searchmuse/sessions.db "SELECT COUNT(*) FROM research_sessions;"

# Controllare i processi
ps aux | grep searchmuse
ps aux | grep ollama
```

### Metriche da Monitorare

- **CPU**: Utilizzo di CPU per SearchMuse e Ollama
- **Memoria**: RAM utilizzata (specificamente Ollama)
- **Disco**: Spazio database e log
- **Connessione**: Latenza vers oi servizi esterni
- **Errori**: Tasso di errori nei log
- **Cache**: Hit/miss rate del cache

## Backup e Recovery

### Backup del Database

```bash
# Backup giornaliero
0 2 * * * /usr/bin/sqlite3 /var/lib/searchmuse/sessions.db ".backup /backup/searchmuse-$(date +\%Y\%m\%d).db"

# Backup con compressione
0 2 * * * /bin/sh -c 'sqlite3 /var/lib/searchmuse/sessions.db ".backup /tmp/backup.db" && gzip -c /tmp/backup.db > /backup/searchmuse-$(date +\%Y\%m\%d).db.gz'
```

### Recovery

```bash
# Restore da backup
sqlite3 /var/lib/searchmuse/sessions.db ".restore /backup/searchmuse-YYYYMMDD.db"

# O, se corrotto, ricrearlo
rm /var/lib/searchmuse/sessions.db
searchmuse init-db
```

## Troubleshooting di Produzione

### Ollama Non Raggiungibile

```bash
# Verificare che sia in esecuzione
systemctl status ollama.service

# Controllare i log
journalctl -u ollama.service -n 50

# Riavviare
systemctl restart ollama.service
```

### Creazione di Sessioni Lente

```bash
# Ridurre il numero di iterazioni
SEARCHMUSE_RESEARCH_MAX_ITERATIONS=2

# Disabilitare lo scraping
SEARCHMUSE_SCRAPER_DISABLE_IMAGES=true
SEARCHMUSE_SCRAPER_DISABLE_CSS=true

# Ridurre timeout ricerca
SEARCHMUSE_SEARCH_MAX_RESULTS_PER_ITERATION=5
```

### Database Bloccato

```bash
# Riavviare il servizio
systemctl restart searchmuse.service

# Se persiste, controllare file lock
ls -la /var/lib/searchmuse/sessions.db*

# Force cleanup (cautela!)
rm /var/lib/searchmuse/sessions.db-journal
```

## Best Practice Produzione

1. **Monitoring**: Configura monitoraggio dei log e alerts
2. **Backup**: Esegui backup giornalieri del database
3. **Updates**: Pianifica gli aggiornamenti fuori dai picchi di utilizzo
4. **Capacity Planning**: Monitora la crescita del database
5. **Security**: Usa firewall e limita l'accesso
6. **Resource Limits**: Imposta limiti di CPU/memoria
7. **Error Handling**: Configura alert per errori critici
8. **Load Balancing**: Per multi-istanza, usa load balancer

---

**Versione**: 1.0
**Ultimo Aggiornamento**: Febbraio 2026
**Stato**: Stabile
