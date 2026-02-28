# SearchMuse Deployment Guide

Complete guide to deploying SearchMuse in production environments, including Docker setup, systemd configuration, monitoring, and operational best practices.

## Hardware Requirements

### Minimum Configuration

- **CPU**: 2 cores (x86-64)
- **RAM**: 4GB total
  - ~1GB for SearchMuse application
  - ~3GB for Ollama model (mistral)
- **Storage**: 20GB
  - ~3GB for small Ollama models
  - ~5GB for database and logs
- **Network**: 10 Mbps connection

### Recommended Configuration

- **CPU**: 4+ cores
- **RAM**: 8GB total (16GB preferred for mixtral model)
- **Storage**: 100GB SSD
- **Network**: 100+ Mbps

### Model Memory Requirements

| Model | Size | RAM Needed | Notes |
|-------|------|-----------|-------|
| mistral | 7B | 3-4GB | Recommended, fast |
| neural-chat | 7B | 3-4GB | Good for queries |
| llama2 | 13B | 6-8GB | Higher quality |
| mixtral | 8x7B | 32GB | Best quality |

## Docker Deployment

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- At least 4GB available memory

### Docker Compose Setup

Create `docker-compose.yml`:

```yaml
version: '3.9'

services:
  # Ollama LLM service
  ollama:
    image: ollama/ollama:latest
    container_name: searchmuse-ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    environment:
      - OLLAMA_HOST=0.0.0.0:11434
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11434/api/tags"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    restart: unless-stopped

  # SearchMuse application
  searchmuse:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: searchmuse-app
    ports:
      - "8000:8000"
    depends_on:
      ollama:
        condition: service_healthy
    environment:
      - SEARCHMUSE_LLM_PROVIDER=ollama
      - SEARCHMUSE_OLLAMA_BASE_URL=http://ollama:11434
      - SEARCHMUSE_REPOSITORY_TYPE=sqlite
      - SEARCHMUSE_LOGGING_LEVEL=INFO
      - SEARCHMUSE_LOGGING_FILE=/app/logs/searchmuse.log
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./config/production.yaml:/app/config/production.yaml
    command: >
      sh -c "searchmuse --config /app/config/production.yaml research"
    healthcheck:
      test: ["CMD", "searchmuse", "--version"]
      interval: 60s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  # PostgreSQL (optional, for production databases)
  postgres:
    image: postgres:16-alpine
    container_name: searchmuse-db
    environment:
      POSTGRES_DB: searchmuse
      POSTGRES_USER: searchmuse
      POSTGRES_PASSWORD: ${DB_PASSWORD:-changeme}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U searchmuse"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

volumes:
  ollama_data:
  postgres_data:
```

### Dockerfile

Create `Dockerfile`:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Create data and logs directories
RUN mkdir -p /app/data /app/logs

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD searchmuse --version || exit 1

# Default command
CMD ["searchmuse", "--help"]
```

### Deployment Steps

```bash
# 1. Clone repository
git clone https://github.com/yourorg/searchmuse.git
cd searchmuse

# 2. Create environment file
cat > .env << EOF
DB_PASSWORD=secure_password_here
SEARCHMUSE_LOGGING_LEVEL=INFO
EOF

# 3. Pull Ollama model
docker-compose pull ollama
docker-compose run ollama ollama pull mistral

# 4. Start services
docker-compose up -d

# 5. Verify services
docker-compose ps
curl http://localhost:11434/api/tags  # Check Ollama
docker exec searchmuse-app searchmuse --version

# 6. View logs
docker-compose logs -f searchmuse
```

## Systemd Service Deployment

For Linux servers without Docker:

### Create Virtual Environment

```bash
# Create application directory
sudo mkdir -p /opt/searchmuse
sudo chown $USER:$USER /opt/searchmuse

# Clone and install
cd /opt/searchmuse
git clone https://github.com/yourorg/searchmuse.git .
python -m venv venv
source venv/bin/activate
pip install -e .
```

### Create Systemd Service

Create `/etc/systemd/system/searchmuse.service`:

```ini
[Unit]
Description=SearchMuse Research Assistant
After=network.target ollama.service
Wants=ollama.service

[Service]
Type=simple
User=searchmuse
Group=searchmuse
WorkingDirectory=/opt/searchmuse
Environment="PATH=/opt/searchmuse/venv/bin"
Environment="SEARCHMUSE_CONFIG=/opt/searchmuse/config/production.yaml"
Environment="SEARCHMUSE_LOGGING_FILE=/var/log/searchmuse/research.log"
ExecStart=/opt/searchmuse/venv/bin/searchmuse research
Restart=on-failure
RestartSec=10

# Security settings
PrivateTmp=yes
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=/var/log/searchmuse /opt/searchmuse/data

[Install]
WantedBy=multi-user.target
```

### Create Ollama Systemd Service

Create `/etc/systemd/system/ollama.service`:

```ini
[Unit]
Description=Ollama LLM Service
After=network.target

[Service]
Type=simple
User=ollama
Group=ollama
Environment="OLLAMA_HOST=0.0.0.0:11434"
ExecStart=/usr/bin/ollama serve
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Enable and Start Services

```bash
# Create searchmuse user
sudo useradd -r -s /bin/false searchmuse

# Create ollama user
sudo useradd -r -s /bin/false ollama

# Create log directory
sudo mkdir -p /var/log/searchmuse
sudo chown searchmuse:searchmuse /var/log/searchmuse

# Enable services
sudo systemctl daemon-reload
sudo systemctl enable ollama.service
sudo systemctl enable searchmuse.service

# Start services
sudo systemctl start ollama.service
sudo systemctl start searchmuse.service

# Check status
sudo systemctl status searchmuse.service
sudo systemctl status ollama.service

# View logs
sudo journalctl -u searchmuse -f
```

## Monitoring and Health Checks

### Service Health Checks

```bash
# Check Ollama connectivity
curl -s http://localhost:11434/api/tags | jq .

# Check application version
searchmuse --version

# Monitor resource usage
docker stats searchmuse-app  # Docker
top -u searchmuse  # Systemd

# Check database health
sqlite3 /opt/searchmuse/data/searchmuse.db "SELECT COUNT(*) FROM sources;"
```

### Log Monitoring

```bash
# View application logs
tail -f /var/log/searchmuse/research.log

# Filter errors
grep ERROR /var/log/searchmuse/research.log

# Log statistics
wc -l /var/log/searchmuse/research.log
du -h /var/log/searchmuse/
```

### Prometheus Metrics (Optional)

Add metrics export to configuration:

```yaml
# config/production.yaml
monitoring:
  prometheus_enabled: true
  metrics_port: 8001
  metrics_namespace: searchmuse
```

Then scrape with Prometheus:

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'searchmuse'
    static_configs:
      - targets: ['localhost:8001']
```

## Production Configuration

### Optimized config/production.yaml

```yaml
# Optimized for production
search:
  engine: duckduckgo
  results_per_query: 5
  max_total_results: 30
  relevance_threshold: 0.7
  rate_limit_ms: 2000

llm:
  provider: ollama
  model: mistral
  ollama:
    base_url: http://ollama:11434
    timeout_seconds: 60
  temperature: 0.5

scraper:
  default: httpx
  timeout_seconds: 15
  retry_attempts: 2
  rate_limit_ms: 500

repository:
  type: postgres
  postgres:
    host: ${DB_HOST}
    port: 5432
    database: searchmuse
    user: ${DB_USER}
    password: ${DB_PASSWORD}
  cleanup_older_than_days: 30

limits:
  max_iterations: 3
  max_sources_per_iteration: 10
  max_concurrent_scrapes: 3

logging:
  level: WARNING
  file: /var/log/searchmuse/research.log
  max_file_size_mb: 100
  backup_count: 10

timeouts:
  total_research: 300
  per_iteration: 60
```

### Environment Variables

```bash
# Security
export SEARCHMUSE_REPOSITORY_POSTGRES_PASSWORD=$(aws secretsmanager get-secret-value --secret-id searchmuse/db-password --query SecretString --output text)

# Database
export SEARCHMUSE_REPOSITORY_POSTGRES_HOST=db.example.com
export SEARCHMUSE_REPOSITORY_POSTGRES_USER=searchmuse_prod

# Logging
export SEARCHMUSE_LOGGING_LEVEL=WARNING
export SEARCHMUSE_LOGGING_FILE=/var/log/searchmuse/research.log

# Performance
export SEARCHMUSE_LIMITS_MAX_CONCURRENT_SCRAPES=5
```

## Database Management

### SQLite Backup

```bash
# Backup database
sqlite3 /opt/searchmuse/data/searchmuse.db .dump > backup_$(date +%Y%m%d).sql

# Restore from backup
sqlite3 /opt/searchmuse/data/searchmuse.db < backup_20240228.sql

# Vacuum (optimize database file)
sqlite3 /opt/searchmuse/data/searchmuse.db VACUUM;
```

### PostgreSQL Backup

```bash
# Backup database
pg_dump -h localhost -U searchmuse searchmuse > backup_$(date +%Y%m%d).sql

# Restore from backup
psql -h localhost -U searchmuse searchmuse < backup_20240228.sql

# Continuous replication (optional)
# Use WAL archiving for point-in-time recovery
```

## Scaling Considerations

### Horizontal Scaling

For multiple SearchMuse instances:

1. Use PostgreSQL instead of SQLite
2. Implement distributed task queue (Celery + Redis)
3. Load balance with Nginx or HAProxy
4. Use shared Ollama service (single instance)

Example Nginx configuration:

```nginx
upstream searchmuse {
    server searchmuse-1:8000;
    server searchmuse-2:8000;
    server searchmuse-3:8000;
}

server {
    listen 80;
    location / {
        proxy_pass http://searchmuse;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Rate Limiting

In production.yaml:

```yaml
limits:
  max_concurrent_requests: 10
  requests_per_minute: 100
```

## Security Checklist

Before deploying to production:

- [ ] All secrets in environment variables, not config files
- [ ] Database password is strong (20+ chars, random)
- [ ] SSL/TLS enabled for all external connections
- [ ] Firewall rules restrict access (only needed ports)
- [ ] Regular backups tested and verified
- [ ] Log rotation configured
- [ ] Health checks monitoring
- [ ] Rate limiting enabled
- [ ] robots.txt respected
- [ ] User-Agent header includes contact info

See [Security Guide](009_security.md) for details.

## Troubleshooting

### Service won't start

```bash
# Check service status
sudo systemctl status searchmuse
sudo journalctl -u searchmuse -n 50

# Verify dependencies
ollama list  # Ollama running?
curl http://localhost:11434/api/tags  # Ollama accessible?

# Check permissions
ls -la /opt/searchmuse/data
ls -la /var/log/searchmuse
```

### High memory usage

```bash
# Check memory by service
docker stats  # Docker
ps aux | grep searchmuse  # Systemd

# Reduce concurrent operations in config
limits:
  max_concurrent_scrapes: 2

# Reduce batch size
search:
  results_per_query: 5
```

### Slow responses

```bash
# Monitor performance
docker exec searchmuse-app searchmuse --profile

# Check database
sqlite3 data/searchmuse.db "ANALYZE;"

# Increase timeout
timeouts:
  per_iteration: 120
```

## Related Documentation

- [Security Guide](009_security.md) - Security considerations
- [Configuration Reference](005_configuration-reference.md) - All config options
- [Development Setup](006_development-setup.md) - Local development
- [Components Guide](002_components.md) - Architecture overview

---

Last updated: 2026-02-28
