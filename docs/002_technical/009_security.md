# SearchMuse Security Guide

Security considerations and best practices for using SearchMuse safely. This guide covers input validation, web scraping ethics, LLM security, data protection, and supply chain security.

## Overview

SearchMuse operates in security-sensitive areas:
- **Web scraping** - accessing external websites
- **LLM interaction** - using local language models
- **Data collection** - storing sources and content
- **User input** - processing research queries

This guide mitigates risks in each area.

## Input Validation

### Query Validation

All user queries are validated before processing:

```python
from searchmuse.domain import SearchQuery, ValidationError

# Validation rules:
# - Non-empty (after trimming whitespace)
# - Maximum 1000 characters
# - No invalid characters (some reserved for LLM prompts)
# - Language code is 2-letter ISO standard

try:
    query = SearchQuery(
        text="What is machine learning?",
        max_iterations=3,
        timeout_seconds=300,
        language="en"
    )
except ValidationError as e:
    print(f"Invalid query: {e}")
    # Handle validation error
```

### URL Validation

All URLs are validated before scraping:

```python
from searchmuse.adapters.httpx_scraper import validate_url

# Validation rules:
# - Must be valid HTTP(S) URL
# - Must not be localhost or private IP range
# - Must not exceed URL length limits

try:
    if validate_url("https://example.com"):
        # Safe to scrape
        content = await scraper.scrape("https://example.com")
except ValidationError:
    # Invalid or unsafe URL
```

### Content Validation

Extracted content is validated:

- **HTML size limits**: Rejects oversized documents (>100MB)
- **Encoding detection**: Validates text encoding
- **Content type checking**: Verifies HTML/text content
- **Malformed HTML handling**: Uses robust parsers (beautifulsoup4)

## Web Scraping Ethics

### Robots.txt Compliance

SearchMuse respects `robots.txt` by default:

```yaml
# config/default.yaml
search:
  respect_robots_txt: true
```

**How it works:**
1. Fetches `/robots.txt` for each domain
2. Parses User-Agent directives
3. Rejects requests to disallowed paths
4. Logs violations

**Example:**
```
User-agent: *
Disallow: /private/
Disallow: /admin/

User-agent: SearchMuse
Allow: /
```

SearchMuse identifies as "SearchMuse" in requests, allowing sites to specifically allow or deny access.

### Rate Limiting

Respects site capacity and prevents abuse:

```yaml
# config/production.yaml
search:
  rate_limit_ms: 2000      # Min 2 seconds between domain requests
scraper:
  timeout_seconds: 10       # Timeout prevents hanging requests
limits:
  max_concurrent_scrapes: 3 # Limit concurrent requests
```

**Implementation:**
- Tracks last request to each domain
- Enforces minimum delay between requests
- Fails gracefully if overloaded
- Logs rate limit events

### User-Agent Header

Clearly identifies SearchMuse in requests:

```yaml
# config/default.yaml
scraper:
  user_agent: >
    Mozilla/5.0 SearchMuse/1.0 (+https://github.com/yourorg/searchmuse)
```

**Includes:**
- Product name (SearchMuse)
- Version number
- Contact URL

Allows sites to:
- Identify automated research tools
- Block if needed
- Contact maintainers if issues arise

### Acceptable Use Policy

Recommended guidelines for responsible scraping:

1. **Check site's Terms of Service** - Some sites prohibit scraping
2. **Limit frequency** - Don't hammer servers
3. **Identify yourself** - Use meaningful User-Agent
4. **Respect licensing** - Check content copyright
5. **Cache results** - Avoid redundant requests
6. **Handle errors gracefully** - Don't retry aggressively

## LLM Security

### Prompt Injection Prevention

SearchMuse protects against prompt injection attacks:

**Vulnerable approach:**
```python
# WRONG - Direct string interpolation
prompt = f"Assess relevance: {user_query}"
# If user_query = "test' OR 1=1 --", injection possible
```

**Protected approach:**
```python
# Correct - Template with safe placeholders
ASSESSMENT_PROMPT = """
Assess relevance of this query to the source.

Query: {query}
Source: {source_title}

Score: """

prompt = ASSESSMENT_PROMPT.format(
    query=query.text,  # Already validated
    source_title=source.title  # From trusted source
)
```

**Additional protection:**
- Input validation (see Input Validation section)
- Query length limits (max 1000 chars)
- Sanitization of special characters
- System prompts locked (not user-configurable)

### Model Security

Ollama provides security by default:

- **Local execution** - Models run on your hardware, not cloud
- **Offline capable** - No network required after setup
- **Transparent prompting** - You see all prompts sent to LLM
- **No data transmission** - Queries never sent to external servers

**Recommendation:** Use Ollama with trusted models:
- `mistral` - Open source, reviewed
- `neural-chat` - Open source, Intel-sponsored
- `llama2` - Open source, Meta-released
- Avoid: Unknown or suspicious models

### Inference Verification

Verify LLM responses in production:

```python
# config/production.yaml
llm:
  verify_responses: true
  validation_rules:
    # Reject responses with suspicious patterns
    - pattern: "(?i)delete.*database"
      action: reject
    - pattern: "(?i)system.*password"
      action: log_and_reject
```

## Data Storage Security

### SQLite Limitations

SQLite is suitable for development/small deployments:

**Limitations:**
- Single-file database (less secure)
- No user authentication
- No encryption at rest
- No network isolation

**Safe usage:**
```bash
# Restrict file permissions
chmod 600 data/searchmuse.db

# Regular backups
cp data/searchmuse.db backup_$(date +%Y%m%d).db

# Check for suspicious access
ls -la data/searchmuse.db
```

### PostgreSQL for Production

For production, use PostgreSQL:

```yaml
# config/production.yaml
repository:
  type: postgres
  postgres:
    host: db.example.com      # Not localhost
    port: 5432
    database: searchmuse
    user: searchmuse           # Non-admin user
    password: ${DB_PASSWORD}   # From environment
    ssl_mode: require          # Enforce SSL
```

**Security features:**
- User authentication
- Role-based access control
- Connection encryption (SSL)
- Audit logging
- Regular backups with verification

### No Sensitive Data Storage

SearchMuse stores only:
- **Source URLs and metadata** (public)
- **Extracted article content** (from public web)
- **Research queries** (your own)

Never stores:
- Passwords or authentication credentials
- API keys (except in config, never in DB)
- Personal information
- Sensitive research (implement application-level encryption if needed)

## Dependency Security

### Supply Chain Security

All dependencies are reviewed for security:

```bash
# Check for known vulnerabilities
pip install safety
safety check

# Or use pip-audit
pip install pip-audit
pip-audit

# Check outdated packages
pip list --outdated

# Review dependency tree
pip install pipdeptree
pipdeptree
```

### Trusted Dependencies

Core dependencies chosen for maturity and security:

| Package | Purpose | Trust Level | Notes |
|---------|---------|------------|-------|
| httpx | HTTP client | High | Async-first, well-maintained |
| playwright | Browser automation | High | Microsoft-backed |
| trafilatura | Content extraction | High | Actively maintained |
| ollama | LLM integration | High | Official Ollama library |
| typer | CLI framework | High | Fast API creator |
| pytest | Testing | High | Industry standard |

### Dependency Pinning

Production deployments should pin versions:

```python
# pyproject.toml
dependencies = [
    "httpx==0.25.2",          # Specific version
    "ollama==0.1.0",
    "trafilatura==1.6.3",
]

# Not:
# "httpx>=0.25",            # Too loose
# "httpx<1.0",              # Too loose
```

## Configuration Security

### Secrets Management

Never hardcode secrets:

```python
# WRONG
config = {
    "db_password": "super_secret_password",
    "api_key": "sk-1234567890"
}

# CORRECT
config = {
    "db_password": os.environ["DB_PASSWORD"],
    "api_key": os.environ["SEARCHMUSE_API_KEY"]
}
```

### Configuration File Permissions

```bash
# Restrict config file permissions
chmod 600 config/production.yaml

# Verify only owner can read
ls -la config/production.yaml
# -rw------- 1 searchmuse searchmuse 2048 Feb 28 config/production.yaml
```

### Environment Variable Prefix

All SearchMuse variables use `SEARCHMUSE_` prefix:

```bash
# Recommended
export SEARCHMUSE_LLM_MODEL=mistral
export SEARCHMUSE_REPOSITORY_POSTGRES_PASSWORD=secret

# Avoid (too generic)
# export DB_PASSWORD=secret
# export API_KEY=token
```

## Logging and Monitoring

### Secure Logging

Logs should never contain sensitive data:

```python
# WRONG - Logs include password
logger.info(f"Connecting to DB: {connection_string}")
# Output: "Connecting to DB: postgres://user:password@host/db"

# CORRECT - Scrub sensitive data
logger.info(f"Connecting to DB: postgres://user:***@{host}/db")
```

### Audit Logging

For compliance, enable audit logs:

```yaml
# config/production.yaml
logging:
  level: INFO
  file: /var/log/searchmuse/audit.log
  audit_events:
    - repository_access
    - large_queries
    - failed_validations
    - rate_limit_violations
```

### Monitoring Alerts

Set up alerts for security events:

```python
# Monitor for:
- Multiple validation failures (DoS attempt?)
- Unusual query patterns
- Rate limit violations
- Database access anomalies
- Failed authentication
```

## Security Checklist

Before deploying to production:

- [ ] All queries validated (length, characters)
- [ ] All URLs validated (HTTP(S), not private)
- [ ] robots.txt respected
- [ ] Rate limiting configured
- [ ] User-Agent header configured
- [ ] No hardcoded secrets
- [ ] Secrets in environment variables
- [ ] Database credentials strong (20+ chars)
- [ ] SSL/TLS enabled for external connections
- [ ] Log files don't contain sensitive data
- [ ] File permissions restricted (600 for sensitive files)
- [ ] Regular backups tested
- [ ] Dependencies reviewed for CVEs
- [ ] Dependency versions pinned
- [ ] Monitoring and alerts configured
- [ ] Incident response plan documented

## Incident Response

### Security Issue Found

1. **Stop the bleeding**: Disable affected service if needed
2. **Assess scope**: What data may be affected?
3. **Notify stakeholders**: Affected users, team
4. **Patch and test**: Apply security fix, test thoroughly
5. **Deploy fix**: Roll out to production carefully
6. **Document**: Root cause analysis, lessons learned
7. **Rotate secrets**: If credentials compromised

### Reporting Security Issues

If you discover a vulnerability:

1. **Do not disclose publicly** - Email security@example.com
2. **Include details**: Vulnerability, impact, reproduction
3. **Give timeline**: When will you disclose if not fixed?
4. **Work with maintainers**: Coordinate fix and disclosure

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/) - Web security risks
- [CWE Top 25](https://cwe.mitre.org/top25/) - Common weaknesses
- [Google Cloud Security Best Practices](https://cloud.google.com/security/best-practices)
- [Python Security](https://python.readthedocs.io/en/stable/library/security_warnings.html)

## Related Documentation

- [Configuration Reference](005_configuration-reference.md) - Secure configuration
- [Deployment Guide](008_deployment.md) - Production security
- [Development Setup](006_development-setup.md) - Local security
- [Contributing Guide](010_contributing.md) - Code review standards

---

Last updated: 2026-02-28
Security Maintainer: [Contact information]
Vulnerability Reporting: security@example.com
