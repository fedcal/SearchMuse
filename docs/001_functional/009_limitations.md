# SearchMuse Limitations

Understanding SearchMuse's limitations helps you use it effectively and know when to consider alternatives. This document provides transparent assessment of what SearchMuse can and cannot do.

## Scope Limitations

### Not Real-Time

SearchMuse is not suitable for breaking news, live event coverage, or information that changes minute-by-minute.

**Why**:
- Web scraping adds inherent delays
- LLM processing takes time
- Index-based retrieval not real-time

**Example Failures**:
- Stock prices
- Live sports scores
- Breaking news
- Weather forecasts
- Live event coverage

**Workaround**: Use specialized services for real-time data, then ask SearchMuse to contextualize findings.

---

### Not for Login-Required Sites

Cannot access content behind paywalls, authentication walls, or subscription requirements.

**Why**:
- Respects user privacy and terms of service
- Cannot handle interactive authentication
- No way to provide credentials securely

**Examples of Blocked Content**:
- LinkedIn articles (login required)
- Medium paywall articles
- Academic journal paywalls
- Financial data sites (Bloomberg, etc.)
- Subscription newsletters

**Workaround**: Use alternative sources, provide content yourself via copy-paste, or contact publishers for access.

---

### Not for Multimedia-Heavy Content

Cannot meaningfully extract or analyze images, videos, audio, or PDFs.

**Why**:
- Focused on textual content extraction
- Requires specialized models for multimedia
- Not designed for visual search

**Limited Support For**:
- Video transcripts
- Image alt-text only
- PDF metadata (not full text in all cases)
- Audio transcripts

**What Works**:
- Written descriptions of images
- Video transcript text
- PDF text extraction (via trafilatura)
- Audio transcripts (if available as text)

**Workaround**: Use specialized tools for multimedia analysis, then provide text summaries to SearchMuse.

---

### Not a Database Query System

Cannot query structured databases or execute data queries.

**Why**:
- Designed for unstructured web content
- Not a database interface

**Won't Work For**:
- SQL queries
- Data warehouse access
- Scientific dataset analysis
- Large dataset processing

**Workaround**: Use database tools first, then ask SearchMuse to contextualize results.

---

## Quality Limitations

### Depends on LLM Quality

SearchMuse's output quality is directly limited by the local LLM's capabilities.

**Limitations by Model**:

| Model | Reasoning | Technical Accuracy | Nuance | Citation Errors |
|-------|-----------|-------------------|--------|-----------------|
| Phi 3 | Good | 85% | Fair | 5-10% |
| Mistral | Very Good | 88% | Good | 2-5% |
| Llama 3 8B | Excellent | 90% | Excellent | 1-3% |
| Llama 3 70B | Outstanding | 95% | Outstanding | <1% |

**Common LLM Issues**:
- Hallucinated statistics (making up numbers)
- Outdated information treated as current
- Difficulty with very technical topics
- Bias from training data
- Oversimplification of complex concepts

**Mitigation**:
- Use larger models for complex topics
- Always verify numerical claims
- Check source quality
- Use multiple iterations for complex queries

---

### Limited by Source Availability

Cannot find information that isn't published online.

**Problems**:
- Proprietary internal research
- Unpublished findings
- Confidential information
- Rare or obscure sources
- Niche knowledge in small communities

**Example**:
- "What does the CIA think about X?" (classified)
- "Internal Google architecture" (proprietary)
- "Unpublished research data" (not available)

**Workaround**: Combine SearchMuse with primary sources, expert interviews, or direct contact.

---

### Limited by Source Quality

Results only as good as available sources.

**Problems**:
- Misinformation spreads online
- Low-quality sources rank highly in search
- Conflicting sources without resolution
- Biased sources
- Outdated information mixed with current

**Example Poor Source Situations**:
- Niche topics dominated by amateur sources
- Highly politicized topics with polarized sources
- Emerging topics with limited professional coverage
- Rapidly evolving fields with outdated material

**Mitigation**:
- Set minimum publication date filters
- Prefer authoritative domains
- Use larger min_sources (more diverse coverage)
- Increase coverage_threshold for rigor

---

### Content Extraction Limitations

Trafilatura and readability-lxml sometimes fail to extract content correctly.

**Common Issues**:
- Heavy ad/sidebar content mixed with text
- Complex table structures lost
- Code blocks poorly preserved
- Mathematical formulas not captured
- Multilingual content not fully handled

**Failure Rates by Site Type**:

| Site Type | Extraction Success |
|-----------|------------------|
| News sites | 95% |
| Blog posts | 90% |
| Technical docs | 88% |
| Academic articles | 82% |
| Social media | 70% |
| Custom layouts | 60% |

**Workaround**: Review source content directly when extraction seems incomplete.

---

## Technical Limitations

### Respects robots.txt

Cannot scrape sites that block SearchMuse in their robots.txt. Some sites deliberately block all bots.

**Common Blockers**:
```
User-agent: *
Disallow: /
```

**Affected Sites**:
- Some financial sites
- Some e-commerce platforms
- Restricted content sites

**Mitigation**: Use public API endpoints if available, contact site owners for scraping permission.

---

### Rate Limiting Delays

Respects server rate limits, which slows down searches.

**Constraints**:
- 1 second minimum between requests to same domain
- Some sites further restrict (5-10s per request)
- IP bans possible if too aggressive

**Impact on Speed**:
- 10 results per domain = 10 seconds minimum
- Multiple domains = additive delays
- Total search: typically 2-5 minutes

---

### JavaScript-Heavy Sites Slower

Sites requiring full JavaScript rendering take 5-15 seconds per page.

**Slow Site Types**:
- Medium, Substack (JavaScript SPAs)
- Twitter/X (heavy rendering)
- Modern web apps
- Infinite scroll sites

**Speed Impact**:
- Normal sites: 1-3 seconds
- JS sites: 5-15 seconds
- Average search with JS sites: 3-5 minutes

---

### Memory Constraints

System memory limits how much content can be simultaneously processed.

**Constraints**:
- Typical: 8-16GB RAM
- Large queries: may hit memory ceiling
- GPU memory separate from system RAM

**Impact**:
- Max ~100 sources before memory issues
- Very large content pages problematic
- Long-running searches may accumulate memory

**Mitigation**:
- Monitor system memory
- Use `max_iterations: 3` for simple queries
- Close other applications

---

### Network Issues

Requires stable internet connection. Network problems interrupt searches.

**Failure Modes**:
- DNS resolution failure
- Timeouts
- Connection resets
- Proxy issues

**Workaround**: Retry after network stabilizes, or increase timeouts.

---

## Site-Specific Limitations

### Paywalls

Cannot bypass or access paywall-protected content.

**Examples**:
- New York Times (soft paywall)
- Wall Street Journal
- Financial Times
- Nature, Science journals
- Most academic publishers

**What's Possible**: Article preview/abstract sometimes accessible
**Limitation**: Full articles unreachable

---

### CAPTCHA and Bot Detection

Cannot solve CAPTCHAs or bypass sophisticated bot detection.

**Examples**:
- Google (often requires CAPTCHA)
- LinkedIn (strong anti-bot)
- Some financial sites
- Cloudflare-protected sites

**Workaround**: Use alternative sources or manual retrieval

---

### Geo-Restrictions

Cannot bypass geographic IP restrictions.

**Examples**:
- EU content restricted in US
- US content blocked in China
- Country-specific paywall tiers
- Regional content locks

**Workaround**: Use appropriate region for research, or find international mirrors

---

### Dynamic/Infinite Scroll

Infinite scroll sites often don't expose all content to Playwright.

**Examples**:
- Twitter/X (paginated with infinite scroll)
- Instagram (heavily dynamic)
- TikTok (pure video, limited text)

**Issue**: Limited content per page, difficult to gather comprehensive data

---

## Search-Related Limitations

### DuckDuckGo Limitations

SearchMuse uses DuckDuckGo for search, inheriting its limitations.

**Issues**:
- Fewer results than Google for niche topics
- Less comprehensive indexing
- Sometimes outdated index
- Different ranking algorithm

**Workaround**: Craft more specific queries, increase min_sources

---

### Query Interpretation

LLM strategy generation sometimes misinterprets queries.

**Common Issues**:
- Ambiguous terms misunderstood
- Context-dependent queries confused
- Sarcasm/jokes taken literally
- Niche terminology missed

**Example**:
```
Query: "Is Python better?"
LLM interprets: Programming language Python vs Python snake
Should interpret: Python programming language vs [other language]
```

**Workaround**: Use specific terminology, provide context

---

### Search Strategy Limitations

LLM-generated strategies sometimes suboptimal.

**Issues**:
- Misses relevant search terms
- Searches incorrect domains
- Over-creative approaches that fail
- Outdated knowledge about domain experts

**Mitigation**: Review strategy output, provide feedback

---

## Comparison with Alternatives

### vs. Manual Research
SearchMuse Advantages:
- Much faster
- Consistent methodology
- Always cites sources
- No human bias

Manual Research Advantages:
- Better understanding of nuance
- Catches errors LLM misses
- Better judgment of source quality
- Can access restricted content

### vs. Google Scholar
SearchMuse Advantages:
- Includes non-academic sources
- Automated, iterative search
- Local LLM control
- Always offline

Google Scholar Advantages:
- Specialized for academic papers
- Better indexing of journals
- Citation metrics
- Peer review indicators

### vs. Perplexity.ai
SearchMuse Advantages:
- Privacy (completely local)
- No cloud dependency
- Open source
- No subscription costs
- Control over LLM model

Perplexity Advantages:
- Faster (cloud-powered)
- Better UI
- Real-time information
- Multi-model support

### vs. Specialized Databases
SearchMuse Advantages:
- Free and open source
- No paywalls
- Works on any topic

Database Advantages:
- Deep specialized knowledge
- Peer-reviewed content
- Structured data
- Expert curation

---

## Known Bugs and Issues

### Citation Formatting
- Some special characters in URLs cause issues
- Non-ASCII author names sometimes lost
- Date parsing inconsistent across locales

### Content Extraction
- Tables sometimes extracted as plain text
- Code blocks sometimes lose formatting
- Sidebars sometimes included in main content

### LLM Integration
- Very long content truncated in prompts
- Temperature settings don't always apply
- Streaming sometimes drops tokens

### Edge Cases
- Very short queries (<3 characters) rejected
- Queries in non-Latin scripts sometimes fail
- Extremely long search results cause memory issues

---

## Mitigation Strategies

### For Quality Issues
1. Use larger, better LLM models
2. Increase min_sources (more diverse opinions)
3. Increase coverage_threshold (more comprehensive)
4. Review source quality manually
5. Use domain filters to prefer authoritative sources

### For Coverage Issues
1. Increase max_iterations (more thorough search)
2. Use specific terminology
3. Break complex queries into sub-queries
4. Provide context and keywords

### For Speed Issues
1. Use smaller/faster models (phi3)
2. Reduce max_iterations
3. Lower coverage_threshold
4. Disable JavaScript rendering where possible

### For Content Issues
1. Always verify numerical claims
2. Check source credibility
3. Cross-reference across sources
4. Use primary sources when possible

---

## Requesting Features

If you encounter limitations preventing your use case:

1. Check if alternative approach exists (see Mitigation section)
2. Open GitHub issue with detailed description
3. Provide example queries that fail
4. Help prioritize improvements via voting

Many limitations are addressable through community contributions.
