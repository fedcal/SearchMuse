# SearchMuse Testing Strategy

Comprehensive guide to testing philosophy, practices, and patterns in SearchMuse. We follow Test-Driven Development (TDD) with a target coverage of 80%+ across all test types.

## Testing Philosophy

**Test-Driven Development (TDD):** Always write tests before implementation.

1. **RED**: Write failing test for desired behavior
2. **GREEN**: Write minimal implementation to pass test
3. **REFACTOR**: Improve code while tests remain green

Benefits:
- Tests serve as executable specification
- Prevents overengineering
- Enables confident refactoring
- Reduces bugs and regressions

## Test Types

SearchMuse uses three types of tests:

### Unit Tests (40-50% of coverage)

Test individual functions, classes, and methods in isolation.

**Location:** `tests/domain/`, `tests/adapters/`

**Scope:**
- Domain entities and value objects
- Individual port interface methods
- Utility functions
- Business logic

**Example:**

```python
# tests/domain/test_search_query.py
import pytest
from searchmuse.domain import SearchQuery, ValidationError

class TestSearchQuery:
    def test_valid_query_creation(self):
        """SearchQuery should accept valid input."""
        query = SearchQuery(text="quantum computing")
        assert query.text == "quantum computing"
        assert query.max_iterations == 5

    def test_empty_text_raises_validation_error(self):
        """SearchQuery should reject empty text."""
        with pytest.raises(ValidationError):
            SearchQuery(text="")

    def test_max_iterations_must_be_positive(self):
        """SearchQuery should validate max_iterations > 0."""
        with pytest.raises(ValidationError):
            SearchQuery(text="test", max_iterations=0)

    def test_query_is_immutable(self):
        """SearchQuery (frozen dataclass) should be immutable."""
        query = SearchQuery(text="test")
        with pytest.raises(AttributeError):
            query.text = "modified"
```

---

### Integration Tests (30-40% of coverage)

Test interactions between components and with external systems.

**Location:** `tests/integration/`

**Scope:**
- Port-to-adapter contracts
- Multi-component workflows
- Database operations
- API integrations
- Error handling across components

**Example:**

```python
# tests/integration/test_sqlite_repository.py
import pytest
import tempfile
from pathlib import Path
from searchmuse.adapters.sqlite_repository import SQLiteRepository
from searchmuse.domain import Source

@pytest.fixture
async def repository():
    """Create temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        repo = SQLiteRepository(db_path=str(db_path))
        await repo.initialize()
        yield repo
        await repo.close()

class TestSQLiteRepository:
    @pytest.mark.asyncio
    async def test_save_and_retrieve_source(self, repository):
        """Repository should persist and retrieve sources."""
        source = Source(
            url="https://example.com",
            title="Test Source",
            summary="A test source",
            relevance_score=0.95,
            discovered_at=datetime.now()
        )

        await repository.save_source(source)
        retrieved = await repository.find_source("https://example.com")

        assert retrieved is not None
        assert retrieved.url == source.url
        assert retrieved.title == source.title

    @pytest.mark.asyncio
    async def test_source_not_found_returns_none(self, repository):
        """Repository should return None for missing sources."""
        result = await repository.find_source("https://nonexistent.com")
        assert result is None
```

---

### End-to-End Tests (10-20% of coverage)

Test complete workflows from user input to output.

**Location:** `tests/e2e/`

**Scope:**
- Full research workflows
- CLI commands
- Complete orchestration
- Real external service calls (with mocks for rate limiting)

**Example:**

```python
# tests/e2e/test_research_workflow.py
import pytest
from searchmuse.cli import app
from typer.testing import CliRunner

@pytest.fixture
def cli_runner():
    return CliRunner()

class TestResearchWorkflow:
    @pytest.mark.asyncio
    def test_research_command_completes(self, cli_runner, mocker):
        """Research command should execute and return results."""
        # Mock external services
        mocker.patch.object(SearchPort, 'search', return_value=[...])
        mocker.patch.object(ScraperPort, 'scrape', return_value="<html>...")
        mocker.patch.object(LLMPort, 'generate_strategy', return_value="...")

        result = cli_runner.invoke(
            app,
            ["research", "quantum computing", "--max-iterations", "1"]
        )

        assert result.exit_code == 0
        assert "Research Results" in result.stdout
```

## Test Organization

```
tests/
├── conftest.py                    # Shared fixtures
├── domain/                        # Domain entity tests
│   ├── test_search_query.py
│   ├── test_search_state.py
│   ├── test_source.py
│   └── test_citation.py
├── ports/                         # Port contract tests
│   ├── test_llm_port.py
│   ├── test_scraper_port.py
│   └── test_repository_port.py
├── adapters/                      # Adapter tests
│   ├── test_ollama_llm.py
│   ├── test_httpx_scraper.py
│   ├── test_trafilatura_extractor.py
│   └── test_sqlite_repository.py
├── integration/                   # Multi-component tests
│   ├── test_strategy_generation.py
│   ├── test_source_extraction.py
│   └── test_research_iteration.py
├── e2e/                          # End-to-end tests
│   ├── test_research_workflow.py
│   └── test_cli_commands.py
└── fixtures/                      # Test data
    ├── sample_html.html
    ├── sample_responses.json
    └── mock_data.py
```

## Fixtures and Test Utilities

### Shared Fixtures

**File:** `tests/conftest.py`

```python
import pytest
from searchmuse.domain import SearchQuery, Source

@pytest.fixture
def sample_query():
    """Provide a sample search query."""
    return SearchQuery(
        text="What is machine learning?",
        max_iterations=3,
        timeout_seconds=300
    )

@pytest.fixture
def sample_source():
    """Provide a sample source."""
    return Source(
        url="https://example.com/ml",
        title="Introduction to Machine Learning",
        summary="A comprehensive guide to ML",
        relevance_score=0.95,
        discovered_at=datetime.now()
    )

@pytest.fixture
async def mock_llm(mocker):
    """Provide a mocked LLM adapter."""
    mock = mocker.AsyncMock()
    mock.generate_strategy = AsyncMock(
        return_value="machine learning supervised learning neural networks"
    )
    return mock

@pytest.fixture
async def mock_scraper(mocker):
    """Provide a mocked scraper."""
    mock = mocker.AsyncMock()
    mock.scrape = AsyncMock(return_value="<html><body>Content</body></html>")
    return mock
```

### Mock Data

**File:** `tests/fixtures/mock_data.py`

```python
SAMPLE_HTML = """
<!DOCTYPE html>
<html>
<head><title>Test Article</title></head>
<body>
<h1>Article Title</h1>
<p>First paragraph about the topic.</p>
<p>Second paragraph with more details.</p>
</body>
</html>
"""

SAMPLE_SEARCH_RESULTS = [
    {
        "title": "Result 1",
        "url": "https://example.com/1",
        "summary": "First result"
    },
    {
        "title": "Result 2",
        "url": "https://example.com/2",
        "summary": "Second result"
    }
]
```

## Mocking Strategies

### Mocking HTTP Requests (respx)

For testing adapters that use httpx:

```python
import pytest
import respx
from httpx import Response

@pytest.mark.asyncio
async def test_scraper_handles_errors():
    """Scraper should handle HTTP errors gracefully."""
    async with respx.mock:
        # Mock HTTP 404
        respx.get("https://example.com").mock(
            return_value=Response(404)
        )

        scraper = HttpxScraper()
        with pytest.raises(NetworkError):
            await scraper.scrape("https://example.com")

@pytest.mark.asyncio
async def test_scraper_returns_html():
    """Scraper should return HTML content."""
    html_content = "<html><body>Test</body></html>"

    async with respx.mock:
        respx.get("https://example.com").mock(
            return_value=Response(200, text=html_content)
        )

        scraper = HttpxScraper()
        result = await scraper.scrape("https://example.com")
        assert result == html_content
```

### Mocking Port Interfaces

Use Protocol mocks for port testing:

```python
from unittest.mock import AsyncMock
from searchmuse.ports import LLMPort

@pytest.fixture
def mock_llm_port() -> LLMPort:
    """Create a mock LLM port."""
    mock = AsyncMock(spec=LLMPort)
    mock.generate_strategy = AsyncMock(
        return_value="refined search terms"
    )
    mock.synthesize_result = AsyncMock(
        return_value="comprehensive synthesis"
    )
    mock.assess_relevance = AsyncMock(return_value=0.85)
    return mock
```

### Mocking External Services

```python
import pytest
from unittest.mock import patch

@pytest.mark.asyncio
async def test_ollama_fallback():
    """Should handle Ollama connection failure."""
    with patch('ollama.Client') as mock_client:
        mock_client.side_effect = ConnectionError("Ollama unavailable")

        with pytest.raises(SearchError):
            await ollama_adapter.generate_strategy(...)
```

## Running Tests

### Basic Test Execution

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/domain/test_search_query.py

# Run specific test class
pytest tests/domain/test_search_query.py::TestSearchQuery

# Run specific test method
pytest tests/domain/test_search_query.py::TestSearchQuery::test_valid_query

# Run tests matching pattern
pytest -k "test_scraper" tests/

# Run with verbose output
pytest -v tests/

# Run with detailed failure output
pytest --tb=long tests/
```

### Test Coverage

```bash
# Generate coverage report
pytest --cov=searchmuse --cov-report=html tests/

# View coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux

# Show coverage in terminal
pytest --cov=searchmuse --cov-report=term-missing tests/

# Coverage by file
pytest --cov=searchmuse --cov-report=term-missing:skip-covered tests/
```

**Target:** 80%+ overall coverage

### Async Test Execution

```bash
# Run only async tests
pytest -m asyncio tests/

# Run all tests (including async)
pytest tests/
```

SearchMuse uses `pytest-asyncio` for async test support. Decorate async tests:

```python
@pytest.mark.asyncio
async def test_async_operation():
    result = await some_async_function()
    assert result == expected
```

## Test Quality Standards

Every test should:

1. **Have a clear purpose**: What behavior is being tested?
2. **Be independent**: Not depend on other tests' state
3. **Be deterministic**: Always pass or always fail
4. **Be fast**: Complete in <1 second
5. **Have a descriptive name**: `test_<subject>_<behavior>_<expectation>`
6. **Follow Arrange-Act-Assert pattern**:

```python
def test_example():
    # Arrange: Set up test data
    query = SearchQuery(text="test")

    # Act: Perform the action
    result = validate_query(query)

    # Assert: Check the result
    assert result.is_valid
```

## Continuous Integration

Tests run automatically on:

- Every commit (pre-commit hook)
- Every pull request (GitHub Actions)
- Before deployment

See [Contributing Guide](010_contributing.md) for CI/CD details.

## Common Testing Patterns

### Testing Exceptions

```python
def test_raises_validation_error():
    """Should raise ValidationError for invalid input."""
    with pytest.raises(ValidationError) as exc_info:
        SearchQuery(text="")

    assert "text" in str(exc_info.value)
```

### Testing Immutability

```python
def test_frozen_dataclass():
    """Domain objects should be immutable."""
    source = Source(
        url="https://example.com",
        title="Example",
        summary="Summary",
        relevance_score=0.9,
        discovered_at=datetime.now()
    )

    with pytest.raises(AttributeError):
        source.title = "Modified"
```

### Testing Async Operations

```python
@pytest.mark.asyncio
async def test_concurrent_operations():
    """Should handle concurrent scraping."""
    scraper = HttpxScraper()

    tasks = [
        scraper.scrape(f"https://example.com/{i}")
        for i in range(5)
    ]

    results = await asyncio.gather(*tasks)
    assert len(results) == 5
```

## Debugging Tests

```bash
# Run with print output
pytest -s tests/path/to/test.py

# Drop into debugger on failure
pytest --pdb tests/

# Drop into debugger at start of test
pytest --trace tests/path/to/test.py::test_name

# Run with logging
pytest --log-cli-level=DEBUG tests/
```

## Test Performance

Monitor and maintain test speed:

```bash
# Show slowest tests
pytest --durations=10 tests/

# Fail if test takes >1 second
pytest --durations=10 --durations-min=1.0 tests/
```

## Related Documentation

- [Development Setup](006_development-setup.md) - Running tests locally
- [Contributing Guide](010_contributing.md) - PR testing requirements
- [Architecture Overview](001_architecture.md) - How to test the architecture
- [Components Guide](002_components.md) - Component-specific testing patterns

---

Last updated: 2026-02-28
