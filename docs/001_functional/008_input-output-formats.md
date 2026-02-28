# SearchMuse Input/Output Formats

## Input Formats

### Format 1: Simple String Query

**Use Case**: Quick ad-hoc research, simple use cases

**Example**:
```
"What is machine learning?"
```

**Processing**:
- Normalized automatically
- Uses default configuration
- Language auto-detected
- Max 5 iterations

**API Endpoint**:
```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: text/plain" \
  -d "What is machine learning?"
```

---

### Format 2: JSON Query Object

**Use Case**: Advanced use cases, custom parameters, API integration

**Full JSON Schema**:
```json
{
  "query": "machine learning algorithms comparison",
  "language": "en",
  "settings": {
    "max_iterations": 3,
    "min_sources": 5,
    "coverage_threshold": 0.7,
    "output_format": "markdown",
    "citation_format": "markdown",
    "include_excerpt": false
  },
  "filters": {
    "min_year": 2023,
    "exclude_domains": ["pinterest.com", "instagram.com"],
    "prefer_domains": ["arxiv.org", "github.com"]
  }
}
```

**Minimal JSON Example** (only required fields):
```json
{
  "query": "React vs Vue comparison"
}
```

**API Endpoint**:
```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "machine learning algorithms",
    "settings": {
      "max_iterations": 4,
      "output_format": "json"
    }
  }'
```

### JSON Field Descriptions

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| query | string | Yes | - | The research query |
| language | string | No | auto-detect | ISO 639-1 code (en, es, fr) |
| max_iterations | int | No | 5 | Maximum refinement iterations |
| min_sources | int | No | 5 | Minimum acceptable sources |
| coverage_threshold | float | No | 0.7 | Coverage score threshold (0.0-1.0) |
| output_format | string | No | markdown | markdown, json, plaintext, html |
| citation_format | string | No | markdown | markdown, html, apa |
| include_excerpt | bool | No | false | Include source excerpts in output |
| min_year | int | No | - | Only sources from year or later |
| exclude_domains | list | No | [] | Domains to never scrape |
| prefer_domains | list | No | [] | Domains to prioritize |
| timeout | int | No | 300 | Total search timeout in seconds |

---

## Output Formats

### Format 1: Markdown Output (Default)

**Best For**: Reading, documentation, blogs, GitHub

**Example Output**:
```markdown
# Research Results: Machine Learning Algorithms

Machine learning algorithms are computational methods that improve through
experience[1]. The field encompasses three main paradigms: supervised learning,
unsupervised learning, and reinforcement learning[2].

## Supervised Learning

Supervised learning trains models using labeled data[3]. Common algorithms include:

- Linear Regression: Best for continuous value prediction[4]
- Decision Trees: Excellent for classification tasks[5]
- Support Vector Machines: Powerful for complex patterns[6]

## Unsupervised Learning

Unsupervised learning finds patterns in unlabeled data[7].

## Reinforcement Learning

Agents learn through interaction with environments[8].

## References

[1] "Machine Learning", Wikipedia
    URL: https://en.wikipedia.org/wiki/Machine_learning
    Accessed: 2024-02-28

[2] "Types of Machine Learning Algorithms", TechCrunch
    URL: https://techcrunch.example.com/ml-types
    Author: John Smith
    Published: 2024-01-15
    Accessed: 2024-02-28

[3] "Supervised Learning Explained", Medium
    URL: https://medium.example.com/supervised-learning
    Accessed: 2024-02-28

[4] "Linear Regression for Beginners", DataCamp
    URL: https://datacamp.example.com/linear-regression
    Published: 2023-06-20
    Accessed: 2024-02-28

[5] "Decision Trees in Machine Learning", Towards Data Science
    URL: https://towardsdatascience.example.com/decision-trees
    Author: Jane Doe
    Accessed: 2024-02-28

[6] "Support Vector Machines Guide", Scikit-Learn
    URL: https://scikit-learn.org/svm
    Published: 2024-02-01
    Accessed: 2024-02-28

[7] "Unsupervised Learning Methods", ArXiv
    URL: https://arxiv.example.com/unsupervised
    Published: 2023-11-10
    Accessed: 2024-02-28

[8] "Reinforcement Learning Fundamentals", DeepMind
    URL: https://deepmind.example.com/rl-fundamentals
    Published: 2023-09-15
    Accessed: 2024-02-28
```

### API Usage for Markdown:
```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "machine learning algorithms",
    "settings": {"output_format": "markdown"}
  }' \
  --output result.md
```

---

### Format 2: JSON Output

**Best For**: Integration, parsing, programmatic access, structured data

**Complete JSON Schema**:
```json
{
  "status": "success",
  "query": "machine learning algorithms",
  "timestamp": "2024-02-28T14:30:00Z",
  "execution": {
    "iterations": 2,
    "total_sources": 12,
    "total_time_seconds": 45,
    "coverage_score": 0.78
  },
  "content": {
    "title": "Research Results: Machine Learning Algorithms",
    "body": "Machine learning algorithms are computational methods...",
    "sections": [
      {
        "heading": "Supervised Learning",
        "content": "Supervised learning trains models using labeled data..."
      },
      {
        "heading": "Unsupervised Learning",
        "content": "Unsupervised learning finds patterns in unlabeled data..."
      }
    ]
  },
  "citations": [
    {
      "index": 1,
      "source_id": "abc123",
      "url": "https://en.wikipedia.org/wiki/Machine_learning",
      "title": "Machine Learning",
      "author": null,
      "publication_date": "2024-01-10",
      "access_date": "2024-02-28",
      "relevance_score": 0.95
    },
    {
      "index": 2,
      "source_id": "def456",
      "url": "https://techcrunch.example.com/ml-types",
      "title": "Types of Machine Learning Algorithms",
      "author": "John Smith",
      "publication_date": "2024-01-15",
      "access_date": "2024-02-28",
      "relevance_score": 0.87
    }
  ],
  "sources": [
    {
      "source_id": "abc123",
      "url": "https://en.wikipedia.org/wiki/Machine_learning",
      "title": "Machine Learning",
      "author": "Wikipedia Contributors",
      "publication_date": "2024-01-10",
      "access_date": "2024-02-28",
      "domain": "wikipedia.org",
      "relevance_score": 0.95,
      "content_length": 5234,
      "excerpt": "Machine learning is a type of artificial intelligence..."
    }
  ],
  "metadata": {
    "language": "en",
    "unique_domains": 8,
    "average_relevance": 0.89,
    "search_strategy": ["machine learning", "ML algorithms", "supervised learning"]
  }
}
```

### API Usage for JSON:
```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "machine learning algorithms",
    "settings": {
      "output_format": "json",
      "include_excerpt": true
    }
  }' | jq .
```

---

### Format 3: Plain Text Output

**Best For**: Terminal use, simple consumption, email

**Example**:
```
RESEARCH RESULTS: MACHINE LEARNING ALGORITHMS
============================================

Machine learning algorithms are computational methods that improve through
experience. The field encompasses three main paradigms: supervised learning,
unsupervised learning, and reinforcement learning.

SUPERVISED LEARNING

Supervised learning trains models using labeled data. Common algorithms include:

- Linear Regression: Best for continuous value prediction
- Decision Trees: Excellent for classification tasks
- Support Vector Machines: Powerful for complex patterns

UNSUPERVISED LEARNING

Unsupervised learning finds patterns in unlabeled data.

REINFORCEMENT LEARNING

Agents learn through interaction with environments.

REFERENCES

[1] Machine Learning
    Wikipedia
    https://en.wikipedia.org/wiki/Machine_learning
    Accessed: 2024-02-28

[2] Types of Machine Learning Algorithms
    TechCrunch, by John Smith
    https://techcrunch.example.com/ml-types
    Published: 2024-01-15
    Accessed: 2024-02-28
```

### API Usage for Plain Text:
```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "machine learning",
    "settings": {"output_format": "plaintext"}
  }'
```

---

### Format 4: HTML Output

**Best For**: Web publishing, rich formatting, email newsletters

**Example**:
```html
<!DOCTYPE html>
<html>
<head>
  <title>Research Results: Machine Learning Algorithms</title>
  <style>
    body { font-family: sans-serif; margin: 20px; }
    h1 { color: #333; }
    .citation { margin-left: 20px; font-size: 0.9em; }
    .source { background: #f5f5f5; padding: 10px; margin: 10px 0; }
  </style>
</head>
<body>
  <h1>Research Results: Machine Learning Algorithms</h1>

  <p>Machine learning algorithms are computational methods that improve through
  experience<sup><a href="#ref1">[1]</a></sup>. The field encompasses three
  main paradigms: supervised learning, unsupervised learning, and reinforcement
  learning<sup><a href="#ref2">[2]</a></sup>.</p>

  <h2>Supervised Learning</h2>
  <p>Supervised learning trains models using labeled data<sup><a href="#ref3">[3]</a></sup>.
  Common algorithms include:</p>
  <ul>
    <li>Linear Regression: Best for continuous value prediction</li>
    <li>Decision Trees: Excellent for classification tasks</li>
  </ul>

  <h2>References</h2>
  <ol id="references">
    <li id="ref1">
      <strong>Machine Learning</strong><br>
      Wikipedia<br>
      <a href="https://en.wikipedia.org/wiki/Machine_learning">
        https://en.wikipedia.org/wiki/Machine_learning
      </a><br>
      Accessed: 2024-02-28
    </li>

    <li id="ref2">
      <strong>Types of Machine Learning Algorithms</strong><br>
      TechCrunch, by John Smith<br>
      <a href="https://techcrunch.example.com/ml-types">
        https://techcrunch.example.com/ml-types
      </a><br>
      Published: 2024-01-15 | Accessed: 2024-02-28
    </li>
  </ol>
</body>
</html>
```

---

## Error Output Format

All errors use consistent JSON format:

```json
{
  "status": "error",
  "error_type": "QueryTooVague",
  "message": "Query is too vague for meaningful research",
  "details": {
    "query": "stuff",
    "minimum_query_length": 3,
    "provided_length": 5,
    "suggestion": "Please provide more specific search terms"
  },
  "timestamp": "2024-02-28T14:30:00Z",
  "request_id": "req_12345"
}
```

### Error Types

| Error Type | Status Code | Cause |
|-----------|------------|-------|
| QueryTooVague | 400 | Query < 3 characters |
| NoSourcesFound | 400 | Search returned no results |
| ExtractionFailed | 500 | Could not extract from sources |
| TimeoutExceeded | 408 | Search took too long |
| RateLimited | 429 | Too many requests |
| OllamaUnavailable | 503 | LLM service offline |
| InvalidConfiguration | 500 | Configuration error |

---

## Streaming Output

For interactive use, stream results as they're generated:

### Markdown Streaming
```bash
curl -X POST http://localhost:8000/search/stream \
  -H "Content-Type: application/json" \
  -d '{"query": "machine learning"}' \
  -N
```

Output (streaming):
```
# Research Results: Machine Learning

Machine learning is...
[PROGRESS] Retrieved 3 sources
[PROGRESS] Assessing relevance...
...
[PROGRESS] Iteration 1 complete. Coverage: 0.65
[PROGRESS] Refining search...
...
[COMPLETE] Coverage: 0.78 with 12 sources
```

### JSON Event Stream
Each line is a JSON event:
```json
{"type": "started", "query": "machine learning"}
{"type": "sources_retrieved", "count": 5, "iteration": 1}
{"type": "content_extracted", "sources": 5}
{"type": "relevance_assessed", "average_score": 0.82}
{"type": "coverage_assessed", "score": 0.65, "converged": false}
{"type": "iteration_complete", "iteration": 1}
{"type": "strategy_refined", "gaps": ["recent implementations", "practical examples"]}
{"type": "sources_retrieved", "count": 7, "iteration": 2}
...
{"type": "complete", "total_sources": 12, "coverage": 0.78}
```

---

## Configuration for Output

Set output preferences:

```yaml
output:
  # Default output format
  default_format: markdown

  # Citation style
  citation_format: markdown  # or html, apa

  # Include optional fields
  include_excerpt: false
  include_relevance_scores: false
  include_metadata: true

  # Formatting preferences
  markdown:
    heading_level: 1
    include_toc: true
  html:
    include_css: true
    responsive: true
  json:
    pretty_print: true
```

---

## Format Examples by Use Case

### Use Case 1: Blog Post Writing
Input:
```json
{
  "query": "latest trends in web development 2024",
  "settings": {
    "output_format": "markdown",
    "min_year": 2024,
    "include_excerpt": true
  }
}
```

### Use Case 2: API Integration
Input:
```json
{
  "query": "React hooks best practices",
  "settings": {
    "output_format": "json",
    "include_excerpt": true,
    "citation_format": "html"
  }
}
```

### Use Case 3: Academic Paper
Input:
```json
{
  "query": "neural networks applications",
  "settings": {
    "output_format": "markdown",
    "citation_format": "apa",
    "min_sources": 20
  }
}
```

### Use Case 4: Quick CLI Lookup
Input:
```
"What is OAuth?"
```
(Uses all defaults, plain text piped to terminal)
