# SearchMuse Source Citation

## Citation Philosophy

SearchMuse is built on the principle that every claim must be traceable to its source. Citations are not optional metadata added after research; they are fundamental to how the system operates. This approach ensures:

- **Verifiability**: Users can click links and verify claims themselves
- **Transparency**: The chain of evidence is visible
- **Accountability**: Sources are identified and credited
- **Academic Integrity**: Proper attribution standards are met
- **Trust**: Users can assess source quality and bias

## Citation Data Model

Every citation in SearchMuse contains:

```python
Citation = {
    "index": 1,                           # Reference number [1], [2], etc.
    "source_id": "abc123def456",         # Unique identifier (hash of URL)
    "url": "https://example.com/page",   # Full accessible URL
    "title": "Page Title",                # Article or page title
    "author": "John Doe",                 # Author (optional)
    "publication_date": "2024-01-15",    # ISO 8601 format (optional)
    "access_date": "2024-02-28",         # When SearchMuse accessed it
    "domain": "example.com",              # Domain for categorization
    "excerpt": "Quote from source...",   # Brief relevant quote (optional)
    "relevance_score": 0.92               # 0.0-1.0 relevance to query
}
```

## Citation Formats Supported

### Format 1: Markdown (Default)

Standard format for most users. Clean, readable, Git-friendly.

#### Example Output

```markdown
# Research Results: Zero-Knowledge Proofs

Zero-knowledge proofs (ZKPs) allow one party to prove knowledge of a fact
without revealing the fact itself[1]. This cryptographic technique has
become increasingly important in privacy-preserving technologies[2].

## Core Concepts

A ZKP consists of three main properties[3]:
- Completeness: honest prover can convince verifier
- Soundness: dishonest prover cannot convince verifier
- Zero-knowledge: verifier learns nothing but the statement's truth

## Applications

ZKPs are used in blockchain privacy solutions[4], authentication systems[5],
and machine learning privacy[6].

## References

[1] "Zero-Knowledge Proofs", Wikimedia Foundation
    URL: https://en.wikipedia.org/wiki/Zero-knowledge_proof
    Accessed: 2024-02-28

[2] "A Beginner's Guide to ZKPs", Sarah Smith
    URL: https://blog.example.com/zk-guide
    Published: 2024-01-15
    Accessed: 2024-02-28

[3] "Zero-Knowledge Proofs: Mathematical Foundations", Journal of Cryptography
    URL: https://example.org/crypto/zk-math
    Published: 2023-06-20
    Accessed: 2024-02-28

[4] "Privacy in Blockchain with Zero-Knowledge Proofs", Tech Review
    URL: https://techreview.example.com/blockchain-zk
    Author: Jane Doe
    Published: 2024-02-10
    Accessed: 2024-02-28

[5] "Authentication Without Passwords", Security Magazine
    URL: https://securitymag.example.com/zk-auth
    Published: 2023-11-30
    Accessed: 2024-02-28

[6] "Federated Learning with Privacy-Preserving ZKPs", AI Research Today
    URL: https://airesearch.example.com/federated-zk
    Author: Dr. Robert Johnson
    Published: 2024-01-20
    Accessed: 2024-02-28
```

#### Format Specification
- Inline citations: `[1]`, `[2]`, numbered sequentially
- Reference section: After all content
- Each reference on separate lines with metadata
- URLs clickable and complete

---

### Format 2: HTML

For web-based publishing and rich formatting.

#### Example Output

```html
<article>
  <h1>Research Results: Zero-Knowledge Proofs</h1>

  <p>Zero-knowledge proofs (ZKPs) allow one party to prove knowledge of a fact
  without revealing the fact itself<sup><a href="#ref1">[1]</a></sup>. This
  cryptographic technique has become increasingly important in
  privacy-preserving technologies<sup><a href="#ref2">[2]</a></sup>.</p>

  <h2>Core Concepts</h2>
  <p>A ZKP consists of three main properties<sup><a href="#ref3">[3]</a></sup>:</p>
  <ul>
    <li>Completeness: honest prover can convince verifier</li>
    <li>Soundness: dishonest prover cannot convince verifier</li>
    <li>Zero-knowledge: verifier learns nothing but statement truth</li>
  </ul>

  <h2>References</h2>
  <ol id="references">
    <li id="ref1">
      <strong>Zero-Knowledge Proofs</strong>, Wikimedia Foundation
      <br>
      <a href="https://en.wikipedia.org/wiki/Zero-knowledge_proof">
        https://en.wikipedia.org/wiki/Zero-knowledge_proof
      </a>
      <br>
      Accessed: 2024-02-28
    </li>

    <li id="ref2">
      <strong>A Beginner's Guide to ZKPs</strong>, Sarah Smith
      <br>
      <a href="https://blog.example.com/zk-guide">
        https://blog.example.com/zk-guide
      </a>
      <br>
      Published: 2024-01-15 | Accessed: 2024-02-28
    </li>

    <li id="ref3">
      <strong>Zero-Knowledge Proofs: Mathematical Foundations</strong>,
      Journal of Cryptography
      <br>
      <a href="https://example.org/crypto/zk-math">
        https://example.org/crypto/zk-math
      </a>
      <br>
      Published: 2023-06-20 | Accessed: 2024-02-28
    </li>
  </ol>
</article>
```

#### Features
- Superscript reference numbers
- Clickable links between text and references
- Accessible semantic HTML
- Mobile-friendly responsive design

---

### Format 3: APA Style

For academic papers and formal documentation.

#### Example Output

```
Zero-knowledge proofs (ZKPs) allow one party to prove knowledge of a fact
without revealing the fact itself (Wikimedia Foundation, 2024). This
cryptographic technique has become increasingly important in
privacy-preserving technologies (Smith, 2024).

A ZKP consists of three main properties (Journal of Cryptography, 2023):
completeness, soundness, and zero-knowledge properties.

References

Journal of Cryptography. (2023). Zero-knowledge proofs: Mathematical
    foundations. Retrieved from
    https://example.org/crypto/zk-math

Smith, S. (2024). A beginner's guide to zero-knowledge proofs. Retrieved
    from https://blog.example.com/zk-guide

Tech Review. (2024). Privacy in blockchain with zero-knowledge proofs.
    Retrieved from
    https://techreview.example.com/blockchain-zk

Wikimedia Foundation. (2024). Zero-knowledge proof. Retrieved from
    https://en.wikipedia.org/wiki/Zero-knowledge_proof
```

#### Features
- Author-date citation style
- Alphabetized reference list
- Follows APA 7th edition guidelines
- Suitable for academic submissions

---

## Citation Extraction Process

### Step 1: Source Registration
As each source is scraped, register it with metadata.

```python
def register_source(
    url: str,
    html: str,
    retrieved_time: datetime
) -> Source:
    source = Source(
        id=hash_url(url),
        url=url,
        title=extract_title(html),
        author=extract_author(html),
        publication_date=extract_date(html),
        access_date=retrieved_time,
        domain=extract_domain(url)
    )
    citation_registry.add(source)
    return source
```

### Step 2: Claim Extraction
During content extraction, identify specific claims.

```python
def extract_claims(
    content: str,
    source: Source
) -> List[Claim]:
    """Extract distinct claims from source content."""
    claims = []

    # LLM identifies key claims
    claim_texts = llm.extract_claims(content)

    for claim_text in claim_texts:
        claims.append(Claim(
            text=claim_text,
            source_id=source.id,
            confidence=0.95
        ))

    return claims
```

### Step 3: Citation Link Creation
When synthesizing results, link claims to citations.

```python
def create_citation_links(
    synthesis_text: str,
    claims: List[Claim]
) -> Tuple[str, List[Citation]]:
    """Create inline citations in synthesis text."""

    citations = []
    citation_index = 1

    # For each claim mentioned in synthesis
    for claim in claims:
        if claim.text in synthesis_text:
            citation = Citation(
                index=citation_index,
                source_id=claim.source_id,
                url=get_source_url(claim.source_id),
                # ... other fields
            )
            citations.append(citation)

            # Add citation marker to text
            synthesis_text = synthesis_text.replace(
                claim.text,
                f"{claim.text}[{citation_index}]"
            )

            citation_index += 1

    return synthesis_text, citations
```

### Step 4: Format Selection
Apply chosen citation format to output.

```python
def format_citations(
    text: str,
    citations: List[Citation],
    format_type: str = "markdown"
) -> str:
    """Format citations according to selected style."""

    if format_type == "markdown":
        return format_markdown(text, citations)
    elif format_type == "html":
        return format_html(text, citations)
    elif format_type == "apa":
        return format_apa(text, citations)
    else:
        raise ValueError(f"Unknown format: {format_type}")
```

---

## Citation Quality Assurance

### Validation Checks

All citations undergo validation before output:

```python
def validate_citations(citations: List[Citation]) -> List[ValidationError]:
    """Ensure citation quality and completeness."""

    errors = []

    for citation in citations:
        # Check URL accessibility
        if not url_accessible(citation.url):
            errors.append(ValidationError(
                citation_index=citation.index,
                issue="URL not accessible",
                severity="HIGH"
            ))

        # Check for required fields
        if not citation.title:
            errors.append(ValidationError(
                citation_index=citation.index,
                issue="Missing title",
                severity="MEDIUM"
            ))

        # Check for duplicates
        if is_duplicate(citation, citations):
            errors.append(ValidationError(
                citation_index=citation.index,
                issue="Duplicate source",
                severity="LOW"
            ))

    return errors
```

### Hallucination Detection

Verify that citations reference real content, not LLM fabrications:

```python
def detect_hallucinations(
    citations: List[Citation],
    source_content: Dict[str, str]
) -> List[int]:
    """Identify suspicious citations that may be hallucinated."""

    suspicious = []

    for citation in citations:
        content = source_content.get(citation.source_id, "")

        # Check if source actually contains relevant content
        relevance = assess_relevance(content, citation)

        if relevance < 0.3:
            suspicious.append(citation.index)

    return suspicious
```

---

## Citation Configuration

```yaml
citations:
  enabled: true
  default_format: markdown  # markdown, html, or apa
  include_author: true
  include_publication_date: true
  include_access_date: true
  include_excerpt: false
  excerpt_length: 100
  validate_urls: true
  check_hallucinations: true
  min_citation_relevance: 0.3
```

---

## Best Practices

1. **Always Cite**: Every claim requires a source citation
2. **Use Primary Sources**: Prefer original sources over summaries
3. **Verify Dates**: Include publication and access dates
4. **Check URLs**: Ensure citations link to actual content
5. **Avoid Plagiarism**: Paraphrase and cite appropriately
6. **Review Format**: Choose citation format appropriate to your context
7. **Update Regularly**: Recite URLs that change or become inaccessible
