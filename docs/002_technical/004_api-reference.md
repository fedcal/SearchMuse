# SearchMuse API Reference

Complete reference for all domain classes, port interfaces, exceptions, and utility functions in SearchMuse.

## Domain Classes

### SearchQuery

User research request.

```python
@dataclass(frozen=True)
class SearchQuery:
    text: str
    max_iterations: int = 5
    timeout_seconds: int = 300
    language: str = "en"
```

**Fields:**
- `text`: Research question (required, max 1000 chars)
- `max_iterations`: Maximum refinement cycles (default: 5, min: 1, max: 10)
- `timeout_seconds`: Total execution timeout (default: 300, min: 30, max: 3600)
- `language`: Result language code (default: "en", examples: "en", "es", "fr")

**Example:**
```python
query = SearchQuery(
    text="What are the latest advances in quantum computing?",
    max_iterations=3,
    timeout_seconds=600,
    language="en"
)
```

---

### SearchState

Research session progress tracker.

```python
@dataclass(frozen=True)
class SearchState:
    query: SearchQuery
    iteration: int
    previous_results: list[Source]
    gathered_evidence: list[ContentBlock]
    current_strategy: str
    is_complete: bool = False
```

**Fields:**
- `query`: Current search query
- `iteration`: 0-based iteration number
- `previous_results`: Sources from all previous iterations
- `gathered_evidence`: Extracted content blocks
- `current_strategy`: LLM-generated search strategy
- `is_complete`: Whether research is finished

**Example:**
```python
state = SearchState(
    query=query,
    iteration=2,
    previous_results=[source1, source2],
    gathered_evidence=[content_block1],
    current_strategy="quantum computing algorithms superposition",
    is_complete=False
)
```

---

### Source

Discovered web resource with metadata.

```python
@dataclass(frozen=True)
class Source:
    url: str
    title: str
    summary: str
    relevance_score: float
    discovered_at: datetime
    extracted_content: ContentBlock | None = None
```

**Fields:**
- `url`: Source URL (required, must be valid HTTP(S))
- `title`: Page title (required, max 500 chars)
- `summary`: Brief description (required, max 1000 chars)
- `relevance_score`: Relevance rating (0.0-1.0)
- `discovered_at`: Discovery timestamp (auto-set)
- `extracted_content`: Full article content (optional)

**Example:**
```python
source = Source(
    url="https://www.ibm.com/quantum/",
    title="IBM Quantum Computing",
    summary="IBM's quantum computing platform and services",
    relevance_score=0.95,
    discovered_at=datetime.now()
)
```

---

### ContentBlock

Extracted content fragment.

```python
@dataclass(frozen=True)
class ContentBlock:
    text: str
    source_url: str
    blocks: list[ContentBlock] = field(default_factory=list)
    metadata: dict[str, str] = field(default_factory=dict)
```

**Fields:**
- `text`: Content text (required, max 100,000 chars)
- `source_url`: Origin URL (required)
- `blocks`: Child blocks (paragraphs, sections)
- `metadata`: Key-value metadata (author, date, etc.)

**Example:**
```python
content = ContentBlock(
    text="Quantum computing leverages quantum mechanics...",
    source_url="https://www.ibm.com/quantum/",
    metadata={
        "author": "IBM Research",
        "published": "2024-01-15",
        "type": "article"
    }
)
```

---

### Citation

Formal source reference.

```python
@dataclass(frozen=True)
class Citation:
    source: Source
    page_number: int | None = None
    accessed_at: datetime = field(default_factory=datetime.now)
    quote: str | None = None
```

**Fields:**
- `source`: Referenced source
- `page_number`: Page reference (optional)
- `accessed_at`: Access timestamp (auto-set)
- `quote`: Relevant quote (optional, max 500 chars)

**Methods:**
- `format_apa() -> str`: APA 7th edition format
- `format_chicago() -> str`: Chicago 17th edition format
- `format_mla() -> str`: MLA 9th edition format

**Example:**
```python
citation = Citation(
    source=source,
    page_number=42,
    quote="Quantum supremacy represents...",
    accessed_at=datetime.now()
)
print(citation.format_apa())
# IBM. (2024). IBM Quantum Computing.
# Retrieved from https://www.ibm.com/quantum/
```

---

### ResearchResult

Complete research session output.

```python
@dataclass(frozen=True)
class ResearchResult:
    query: SearchQuery
    synthesis: str
    sources: list[Source]
    citations: list[Citation]
    evidence_blocks: list[ContentBlock]
    execution_time_seconds: float
    total_iterations: int
```

**Fields:**
- `query`: Original search query
- `synthesis`: AI-generated summary
- `sources`: All discovered sources
- `citations`: Formatted references
- `evidence_blocks`: Supporting evidence
- `execution_time_seconds`: Total runtime
- `total_iterations`: Iterations executed

**Methods:**
- `sources_by_relevance() -> list[Source]`: Sorted by relevance score
- `top_k_sources(k: int) -> list[Source]`: Top k sources

**Example:**
```python
result = ResearchResult(
    query=query,
    synthesis="Quantum computing is...",
    sources=[source1, source2, source3],
    citations=[citation1, citation2, citation3],
    evidence_blocks=[content1, content2],
    execution_time_seconds=45.2,
    total_iterations=3
)
```

## Port Interfaces

### LLMPort

Language model service contract.

```python
class LLMPort(Protocol):
    async def generate_strategy(
        self,
        query: SearchQuery,
        previous_results: list[Source],
        iteration: int
    ) -> str:
        """Generate search strategy for current iteration."""
        ...

    async def synthesize_result(
        self,
        query: SearchQuery,
        sources: list[Source],
        evidence: list[ContentBlock]
    ) -> str:
        """Generate final research synthesis."""
        ...

    async def assess_relevance(
        self,
        query: SearchQuery,
        source: Source
    ) -> float:
        """Score source relevance (0.0-1.0)."""
        ...
```

**Return Values:**
- `generate_strategy()`: Search terms string
- `synthesize_result()`: Markdown-formatted summary
- `assess_relevance()`: Float between 0.0 and 1.0

---

### ScraperPort

Web content retrieval.

```python
class ScraperPort(Protocol):
    async def scrape(
        self,
        url: str,
        timeout_seconds: int = 10
    ) -> str:
        """Fetch page content as HTML or text."""
        ...

    async def scrape_with_javascript(
        self,
        url: str,
        timeout_seconds: int = 30
    ) -> str:
        """Fetch page after JS execution."""
        ...

    async def is_accessible(self, url: str) -> bool:
        """Check if URL is reachable."""
        ...
```

**Exceptions:**
- `TimeoutError`: Request exceeded timeout
- `NetworkError`: Connection failed
- `HttpError(status_code)`: HTTP error response

---

### ContentExtractorPort

Content parsing.

```python
class ContentExtractorPort(Protocol):
    async def extract_article(
        self,
        html: str,
        source_url: str
    ) -> ContentBlock:
        """Extract article body."""
        ...

    async def extract_title(self, html: str) -> str:
        """Extract page title."""
        ...

    async def extract_summary(
        self,
        html: str,
        max_length: int = 200
    ) -> str:
        """Extract page summary."""
        ...
```

---

### SourceRepositoryPort

Source persistence.

```python
class SourceRepositoryPort(Protocol):
    async def save_source(self, source: Source) -> None:
        """Store new source."""
        ...

    async def find_source(self, url: str) -> Source | None:
        """Retrieve source by URL."""
        ...

    async def list_sources(
        self,
        query_text: str,
        limit: int = 100
    ) -> list[Source]:
        """List sources for query."""
        ...

    async def update_source(self, source: Source) -> None:
        """Update existing source."""
        ...

    async def delete_source(self, url: str) -> bool:
        """Remove source by URL."""
        ...
```

---

### SearchPort

Search engine integration.

```python
class SearchPort(Protocol):
    async def search(
        self,
        query: str,
        max_results: int = 10,
        language: str = "en"
    ) -> list[Source]:
        """Execute search query."""
        ...

    async def search_similar(
        self,
        source_url: str,
        max_results: int = 5
    ) -> list[Source]:
        """Find similar sources."""
        ...
```

---

### ResultRendererPort

Output formatting.

```python
class ResultRendererPort(Protocol):
    async def render_result(
        self,
        result: ResearchResult
    ) -> str:
        """Format complete result."""
        ...

    async def render_sources(
        self,
        sources: list[Source],
        format: str = "markdown"
    ) -> str:
        """Format sources list."""
        ...

    async def render_citations(
        self,
        citations: list[Citation],
        style: str = "apa"
    ) -> str:
        """Format bibliography."""
        ...
```

## Exceptions

### SearchError (Base Exception)

Base class for all SearchMuse exceptions.

```python
class SearchError(Exception):
    """Base exception for search operations."""
    pass
```

---

### ValidationError

Invalid input data.

```python
class ValidationError(SearchError):
    """Raised when input validation fails."""
    field: str
    message: str
```

**Example:**
```python
try:
    query = SearchQuery(text="")
except ValidationError as e:
    print(f"Invalid {e.field}: {e.message}")
    # Output: Invalid text: Must be non-empty
```

---

### MaxIterationsExceeded

Too many iterations without convergence.

```python
class MaxIterationsExceeded(SearchError):
    """Raised when max iterations exceeded."""
    iterations: int
    max_iterations: int
```

---

### TimeoutError

Operation exceeded timeout.

```python
class TimeoutError(SearchError):
    """Raised when operation times out."""
    timeout_seconds: int
    operation: str
```

---

### NetworkError

Network operation failed.

```python
class NetworkError(SearchError):
    """Raised on network failures."""
    url: str
    status_code: int | None
    message: str
```

---

### ExtractionError

Content extraction failed.

```python
class ExtractionError(SearchError):
    """Raised when content extraction fails."""
    url: str
    reason: str
```

## Enums

### SearchStatus

Research session status.

```python
class SearchStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
```

---

### CitationFormat

Bibliography format style.

```python
class CitationFormat(Enum):
    APA = "apa"
    CHICAGO = "chicago"
    MLA = "mla"
    HARVARD = "harvard"
```

## Type Aliases

```python
# URL string (validated)
URL = str

# Relevance score 0.0-1.0
RelevanceScore = float

# Search strategy terms
Strategy = str

# Rendered output
Output = str
```

## Utility Functions

### validate_url

```python
def validate_url(url: str) -> bool:
    """Check if URL is valid HTTP(S)."""
    # Returns True if valid, raises ValidationError if invalid
```

---

### validate_query

```python
def validate_query(query: SearchQuery) -> bool:
    """Validate all query constraints."""
    # Checks text length, timeout bounds, etc.
```

## Related Documentation

- [Components Guide](002_components.md) - Implementation details
- [Data Flow](003_data-flow.md) - How data transforms
- [Configuration Reference](005_configuration-reference.md) - Runtime configuration

---

Last updated: 2026-02-28
