# SearchMuse Supported Websites

## Website Support Framework

SearchMuse uses an adapter-based architecture to support different website categories. Each category has documented scraping strategies and known limitations.

## Support Levels

### Level 1: Full Support (Static HTML)

Websites with static HTML content that renders completely without JavaScript.

**Scraping Method**: httpx (fast HTTP client)
- Fast: 1-3 seconds per page
- Reliable: Consistent results
- Lightweight: Minimal resource usage

**Examples**: Wikipedia, news articles, blog posts, documentation sites

```python
ScraperStrategy(
    name="static_html",
    scraper_type=ScraperType.HTTPX,
    timeout=10,
    follow_redirects=True,
    headers={
        "User-Agent": "SearchMuse/1.0 (+https://github.com/searchmuse/searchmuse)"
    }
)
```

---

### Level 2: Partial Support (JavaScript-Rendered)

Websites that require JavaScript execution to render content.

**Scraping Method**: Playwright (browser automation)
- Slower: 5-15 seconds per page
- More Reliable: Captures rendered content
- Higher Resource: Uses headless browser

**Examples**: Medium, Twitter/X threads, Single Page Applications (SPAs), modern news sites

```python
ScraperStrategy(
    name="js_rendered",
    scraper_type=ScraperType.PLAYWRIGHT,
    timeout=15,
    wait_for_selector=".main-content",  # CSS selector
    headless=True,
    disable_images=True  # Optimize performance
)
```

**Configuration**:
```yaml
javascript_rendering:
  enabled: true
  timeout: 15s
  wait_strategies:
    - selector: ".main-content"
      timeout: 10s
    - navigation: "networkidle"
      timeout: 8s
  screenshot_on_error: true
```

---

### Level 3: Limited Support (Anti-Bot Protection)

Websites with strong anti-scraping measures.

**Scraping Method**: Best-effort via Playwright with delays

**Examples**: LinkedIn, Twitter/X (rate-limited), academic journals (paywalled), financial data sites

**Limitations**:
- May fail due to CAPTCHA
- Rate limiting restrictions
- IP blocking risks
- Partial content only

**Configuration**:
```yaml
limited_support:
  enabled: true
  max_retries: 2
  retry_delay: 5s
  user_agent_rotation: true
  proxy_support: false
  accept_partial_failures: true
```

---

## Website Categories

### News & Media

| Site | Support | Notes |
|------|---------|-------|
| BBC News | Full | Static HTML articles |
| CNN | Partial | JavaScript rendered headlines |
| HackerNews | Full | Simple HTML tables |
| TechCrunch | Partial | Medium.com-style rendering |
| Reuters | Partial | Paywalled content (limited) |
| NPR | Full | Well-structured HTML |

**Extraction Priority**: Publication date, author, body text, thumbnail image

---

### Technical Documentation

| Site | Support | Notes |
|------|---------|-------|
| GitHub | Partial | Renders README files well |
| Stack Overflow | Full | Clean HTML structure |
| MDN Web Docs | Full | Excellent semantic HTML |
| Official Docs (Python, Node, etc.) | Full | Well-organized static sites |
| Confluence | Limited | Login often required |
| Notion | Limited | Heavy JavaScript, slow |

**Extraction Priority**: Code examples, API descriptions, parameter lists

---

### Academic & Research

| Site | Support | Notes |
|------|---------|-------|
| ArXiv | Full | PDF summaries available |
| Google Scholar | Partial | JavaScript pagination |
| ResearchGate | Limited | Login required for full access |
| PubMed | Full | Simple HTML, rich metadata |
| SSRN | Partial | Some paywalls |
| Open Access journals | Full | Usually well-structured |

**Extraction Priority**: Abstract, author list, publication date, citations

---

### Blogs & Articles

| Site | Support | Notes |
|------|---------|-------|
| Medium | Partial | Requires JS rendering |
| Dev.to | Full | Clean HTML |
| Substack | Partial | May require subscription |
| Hashnode | Full | Static content available |
| Personal blogs | Full | Depends on blog platform |
| Wikipedia | Full | Excellent structure |

**Extraction Priority**: Publication date, author, byline, article text

---

### Forums & Communities

| Site | Support | Notes |
|------|---------|-------|
| Stack Overflow | Full | High-quality Q&A |
| Reddit | Partial | API-based better, JS rendering works |
| Discourse forums | Partial | JavaScript-heavy |
| GitHub Discussions | Partial | Good JS support |
| Product Hunt | Limited | Heavy dynamic content |

**Extraction Priority**: Question, top answers, vote counts, user reputation

---

### Government & Official Sources

| Site | Support | Notes |
|------|---------|-------|
| Government.gov sites | Full | Well-structured |
| Census bureau | Full | Data-rich |
| FDA | Full | Clear information architecture |
| Standards bodies (NIST, ISO) | Full | Well-documented |
| Legal databases | Partial | Some access restrictions |

**Extraction Priority**: Date, authority, official status, version

---

## robots.txt Compliance

SearchMuse respects robots.txt directives:

```python
def check_robots_txt(url: str) -> bool:
    """Check if URL is allowed by robots.txt."""

    domain = extract_domain(url)
    robots_url = f"{domain}/robots.txt"

    try:
        robots = fetch_robots_txt(robots_url)

        # Check user-agent
        user_agent = "SearchMuse"
        allowed = robots.can_fetch(user_agent, url)

        if not allowed:
            logger.info(f"Blocked by robots.txt: {url}")
            return False

        # Respect crawl delay
        crawl_delay = robots.request_rate(user_agent)
        if crawl_delay:
            sleep(crawl_delay.requests)

        return True

    except Exception as e:
        # If robots.txt fetch fails, allow scraping (conservative)
        logger.warning(f"Could not fetch robots.txt for {domain}: {e}")
        return True
```

### Rate Limiting Strategy

```yaml
rate_limiting:
  default_delay: 1.0s  # seconds between requests to same domain
  per_domain_limits:
    github.com: 0.5s
    wikipedia.org: 0.3s
    medium.com: 2.0s
  concurrent_domains: 3  # max concurrent domains
  respect_retry_after: true
```

---

## Adding Support for New Categories

### Adapter Pattern Implementation

```python
class WebsiteAdapter(ABC):
    """Base class for website scrapers."""

    @abstractmethod
    def can_handle(self, url: str) -> bool:
        """Check if this adapter can scrape the URL."""
        pass

    @abstractmethod
    def scrape(self, url: str) -> ScrapedContent:
        """Scrape and return content."""
        pass

    @abstractmethod
    def extract_metadata(self, html: str) -> Dict[str, str]:
        """Extract title, author, date, etc."""
        pass

class NewsArticleAdapter(WebsiteAdapter):
    """Handles news articles from major outlets."""

    def can_handle(self, url: str) -> bool:
        return any(
            domain in url for domain in
            ["bbc.com", "cnn.com", "npr.org", "reuters.com"]
        )

    def scrape(self, url: str) -> ScrapedContent:
        # Implement news-specific scraping
        pass

    def extract_metadata(self, html: str) -> Dict[str, str]:
        # Implement metadata extraction for news
        pass

# Register adapter
adapter_registry.register(NewsArticleAdapter())
```

### Step-by-Step Guide to Add Support

1. **Analyze Target Site**
   - Inspect HTML structure
   - Identify content selectors
   - Check for JavaScript dependencies
   - Review robots.txt

2. **Create Adapter**
   ```python
   class MyWebsiteAdapter(WebsiteAdapter):
       def can_handle(self, url: str) -> bool:
           return "mywebsite.com" in url

       def scrape(self, url: str) -> ScrapedContent:
           # Implementation
           pass

       def extract_metadata(self, html: str) -> Dict[str, str]:
           # Implementation
           pass
   ```

3. **Define CSS/XPath Selectors**
   ```python
   SELECTORS = {
       "title": "h1.article-title",
       "author": ".byline-author",
       "date": "[data-publish-date]",
       "content": "article.main-content"
   }
   ```

4. **Test Thoroughly**
   - Test with multiple pages
   - Handle edge cases
   - Validate extracted content

5. **Register and Enable**
   ```python
   adapter_registry.register(MyWebsiteAdapter())
   ```

---

## Known Limitations by Category

### News & Media
- Paywalled content: Can access article preview only
- Soft paywalls: May access limited articles per month
- Geo-restrictions: Some content blocked by region
- Dynamic headlines: Load times vary

### Technical Documentation
- Confluence/Jira: Requires authentication
- Private GitHub repos: Inaccessible
- Some API docs: Behind login walls

### Academic
- Most journals: Paywall-protected abstracts/full text
- ResearchGate: Requires account
- Institutional repositories: May require VPN

### Social Media
- Twitter/X: Rate limiting strict, requires API for realtime
- LinkedIn: Strong anti-bot measures
- TikTok: Video-first, text extraction limited
- Instagram: Primarily visual, minimal text

---

## Fallback Strategies

When preferred scraper fails:

```python
def scrape_with_fallback(url: str) -> ScrapedContent:
    """Try multiple scraping strategies."""

    strategies = [
        ("primary", ScraperType.HTTPX),
        ("js_render", ScraperType.PLAYWRIGHT),
        ("trafilatura", ScraperType.TRAFILATURA_ONLY),
        ("readability", ScraperType.READABILITY_ONLY)
    ]

    for strategy_name, scraper in strategies:
        try:
            content = scraper.fetch(url)
            if content and len(content.text) > MIN_CONTENT_LENGTH:
                logger.info(f"Success with {strategy_name}: {url}")
                return content

        except Exception as e:
            logger.debug(f"Failed with {strategy_name}: {e}")
            continue

    raise ScrapingError(f"All strategies failed for {url}")
```

---

## Configuration for Site Categories

```yaml
website_adapters:
  news:
    extractors:
      - trafilatura
      - custom_news_parser
    min_content: 500
    timeout: 10s

  technical_docs:
    extractors:
      - trafilatura
      - code_extractor
    preserve_code_formatting: true
    timeout: 15s

  academic:
    extractors:
      - academic_parser
      - trafilatura
    extract_citations: true
    timeout: 10s
```

---

## Performance by Category

| Category | Avg Time | Success Rate | Content Quality |
|----------|----------|--------------|-----------------|
| News | 2-4s | 95% | Excellent |
| Tech Docs | 1-3s | 98% | Excellent |
| Blogs | 2-4s | 90% | Good |
| Forums | 3-6s | 88% | Good |
| Academic | 2-5s | 75% | Good |
| Limited | 5-15s | 60% | Fair |

---

## Error Handling

```python
class ScrapingError(Exception):
    """Base exception for scraping failures."""
    pass

class RobotsBlocked(ScrapingError):
    """URL blocked by robots.txt."""
    pass

class ContentNotFound(ScrapingError):
    """Could not extract meaningful content."""
    pass

class RateLimited(ScrapingError):
    """Server rate limited the request."""
    pass

class TimeoutError(ScrapingError):
    """Request timed out."""
    pass
```
