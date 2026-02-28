# SearchMuse Contributing Guide

Welcome! This guide explains how to contribute code, documentation, and improvements to SearchMuse. We follow best practices for code quality, testing, and collaboration.

## Code of Conduct

This project adheres to a Code of Conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to the maintainers.

## How to Contribute

### Reporting Bugs

1. **Check existing issues** - Avoid duplicates
2. **Provide details**:
   - SearchMuse version
   - Python version
   - Operating system
   - Steps to reproduce
   - Expected vs. actual behavior
3. **Include logs** - Error messages and stack traces
4. **Example code** - Minimal reproduction case

### Suggesting Enhancements

1. **Describe the feature** - What problem does it solve?
2. **Provide examples** - How would users interact with it?
3. **Discuss implementation** - Technical approach
4. **Check impact** - Does it affect other components?

### Contributing Code

Our contribution workflow:

1. **Fork the repository** on GitHub
2. **Create a feature branch** from `main`
3. **Write tests first** (TDD approach)
4. **Implement the feature**
5. **Pass all checks** (tests, linting, typing)
6. **Create a pull request** with clear description
7. **Address review feedback**
8. **Merge to main**

## Development Workflow

### Step 1: Fork and Clone

```bash
# Fork on GitHub (click "Fork" button)

# Clone your fork
git clone https://github.com/yourusername/searchmuse.git
cd searchmuse

# Add upstream remote
git remote add upstream https://github.com/originalorg/searchmuse.git

# Create feature branch
git checkout -b feature/my-feature
```

### Step 2: Set Up Development Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Verify setup
pytest --version
mypy --version
ruff --version
```

See [Development Setup](006_development-setup.md) for detailed instructions.

### Step 3: Write Tests First (TDD)

Always write tests before implementation:

```python
# tests/domain/test_my_feature.py
import pytest
from searchmuse.domain import MyNewClass

class TestMyFeature:
    def test_basic_functionality(self):
        """MyNewClass should do X."""
        obj = MyNewClass(param="value")
        result = obj.some_method()
        assert result == "expected"

    def test_error_handling(self):
        """MyNewClass should raise error on invalid input."""
        with pytest.raises(ValidationError):
            MyNewClass(param="invalid")
```

Run tests to verify they fail:

```bash
pytest tests/domain/test_my_feature.py -v
# Should show FAILED - this is expected (RED phase)
```

### Step 4: Implement the Feature

```python
# src/searchmuse/domain/my_feature.py
from dataclasses import dataclass

@dataclass(frozen=True)
class MyNewClass:
    param: str

    def some_method(self) -> str:
        """Implement feature logic."""
        if not self.param:
            raise ValidationError("param", "Must be non-empty")
        return f"Result: {self.param}"
```

Run tests to verify they pass:

```bash
pytest tests/domain/test_my_feature.py -v
# Should show PASSED (GREEN phase)
```

### Step 5: Refactor

Improve code while keeping tests passing:

```python
# Optimize, extract methods, improve naming
@dataclass(frozen=True)
class MyNewClass:
    param: str

    def __post_init__(self):
        self._validate()

    def _validate(self) -> None:
        if not self.param:
            raise ValidationError("param", "Must be non-empty")

    def some_method(self) -> str:
        """Process the parameter."""
        return f"Result: {self.param}"
```

Run tests again:

```bash
pytest tests/domain/test_my_feature.py -v
# Should still PASS (REFACTOR phase complete)
```

## Code Standards

### Style and Formatting

SearchMuse uses **ruff** for code formatting and linting.

```bash
# Format code automatically
ruff format src/ tests/

# Check for linting issues
ruff check src/ tests/

# Fix some issues automatically
ruff check --fix src/ tests/
```

Configuration in `pyproject.toml`:

```toml
[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP"]
```

### Type Checking

All code must pass **mypy** strict mode:

```bash
mypy src/ tests/ --strict

# Check specific file
mypy src/searchmuse/domain/my_feature.py --strict
```

Configuration in `pyproject.toml`:

```toml
[tool.mypy]
python_version = "3.11"
strict = true
warn_unused_ignores = true
```

### Immutability

**Critical:** All domain objects must be immutable frozen dataclasses:

```python
# Correct - frozen dataclass
@dataclass(frozen=True)
class MyClass:
    field: str

# Wrong - mutable class
class MyClass:
    def __init__(self, field: str):
        self.field = field
```

No mutation of existing objects:

```python
# Wrong
def update_source(source: Source, title: str) -> None:
    source.title = title  # Mutation!

# Correct - return new object
def update_source(source: Source, title: str) -> Source:
    return Source(
        url=source.url,
        title=title,
        summary=source.summary,
        # ... other fields
    )
```

### Function Size

Keep functions small and focused:

```python
# Wrong - too long
def process_sources(sources, query, llm, scraper, extractor):
    # 100+ lines of logic

# Correct - extracted methods
def process_sources(sources: list[Source]) -> list[Source]:
    return [_process_source(s) for s in sources]

def _process_source(source: Source) -> Source:
    # 20-30 lines focused on single responsibility
```

**Target:** Functions under 50 lines

### File Size

Organize code into small, focused files:

```python
# Wrong - 1000-line file with everything
# searchmuse/utils.py (all utilities)

# Correct - organized by feature
# searchmuse/domain/search_query.py
# searchmuse/domain/search_state.py
# searchmuse/adapters/ollama_llm.py
# searchmuse/adapters/httpx_scraper.py
```

**Target:** Files under 400 lines, max 800 lines

### Error Handling

Handle errors explicitly:

```python
# Wrong - silent failure
try:
    result = await scraper.scrape(url)
except Exception:
    pass  # Error silently ignored

# Correct - explicit error handling
try:
    result = await scraper.scrape(url)
except TimeoutError as e:
    logger.error(f"Scrape timeout for {url}: {e}")
    raise SearchError(f"Could not fetch {url}") from e
except NetworkError as e:
    logger.error(f"Network error for {url}: {e}")
    raise SearchError(f"Network unavailable") from e
```

## Testing Requirements

### Test Coverage

Target: **80%+ overall coverage**

```bash
# Generate coverage report
pytest --cov=searchmuse --cov-report=html tests/

# View specific coverage
pytest --cov=searchmuse --cov-report=term-missing tests/ | grep -A 5 "TOTAL"
```

### Test Types

Every feature needs:

1. **Unit tests** - Individual functions/methods
2. **Integration tests** - Multi-component workflows (optional for small features)
3. **E2E tests** - Complete user flows (optional for critical paths)

### Test Conventions

```python
# Test file location: tests/<layer>/<module>/test_<name>.py
# tests/domain/test_search_query.py
# tests/adapters/test_ollama_llm.py

# Test class: Test<ComponentName>
class TestSearchQuery:
    pass

# Test method: test_<subject>_<behavior>_<expectation>
def test_search_query_with_empty_text_raises_error(self):
    pass

# Use descriptive docstrings
def test_search_query_with_empty_text_raises_error(self):
    """SearchQuery should reject empty text."""
    with pytest.raises(ValidationError):
        SearchQuery(text="")
```

See [Testing Strategy](007_testing-strategy.md) for comprehensive testing guide.

## Commit Message Format

Follow conventional commits:

```
<type>: <description>

<optional body>

<optional footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `refactor`: Code refactoring without behavior change
- `docs`: Documentation changes
- `test`: Test additions or modifications
- `chore`: Build, dependencies, or tooling
- `perf`: Performance improvements
- `ci`: CI/CD configuration

**Examples:**

```
feat: add relevance scoring for sources

Implements LLM-based relevance assessment with configurable
threshold. Scores are cached in repository to avoid redundant
API calls.

Closes #42
```

```
fix: handle timeout in scraper gracefully

Previously, network timeouts would crash the entire research session.
Now timeouts are caught and logged, allowing the orchestrator to
continue with other sources.

Fixes #98
```

```
refactor: extract HTTP client to separate module

Improves code organization and testability by separating HTTP
concerns from scraping logic.
```

## Pull Request Process

### Before Creating PR

1. **Update from upstream**:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run all checks**:
   ```bash
   # Format and lint
   ruff format src/ tests/
   ruff check --fix src/ tests/

   # Type check
   mypy src/ tests/ --strict

   # Tests
   pytest --cov=searchmuse tests/

   # Coverage report
   pytest --cov=searchmuse --cov-report=term-missing tests/
   ```

3. **Verify no issues**:
   - All tests pass
   - Coverage >= 80%
   - No mypy errors
   - No ruff warnings

### Creating PR

1. **Push to your fork**:
   ```bash
   git push -u origin feature/my-feature
   ```

2. **Create PR on GitHub**:
   - Clear title describing the feature
   - Reference any related issues (#42, #98)
   - Describe what changed and why
   - Link to relevant documentation

3. **PR Template**:
   ```markdown
   ## Description
   Brief description of changes.

   ## Related Issues
   Closes #42

   ## Changes
   - Item 1
   - Item 2

   ## Testing
   - [ ] Added unit tests
   - [ ] Added integration tests
   - [ ] Manually tested locally

   ## Checklist
   - [ ] Code follows style guide
   - [ ] No new warnings
   - [ ] Tests pass
   - [ ] Coverage >= 80%
   - [ ] Documentation updated
   ```

### During Review

1. **Address feedback** constructively
2. **Make focused commits** for each fix
3. **Re-request review** after addressing comments
4. **Communicate clearly** about changes

### After Merge

1. **Delete feature branch**:
   ```bash
   git branch -d feature/my-feature
   git push origin --delete feature/my-feature
   ```

2. **Update local main**:
   ```bash
   git checkout main
   git pull upstream main
   ```

## Extending with Adapters

### Adding a New Adapter

To add support for a new LLM, scraper, or storage backend:

1. **Define the port** (if new):
   ```python
   # src/searchmuse/ports/my_port.py
   from typing import Protocol

   class MyPort(Protocol):
       async def my_method(self, param: str) -> str:
           """Docstring."""
           ...
   ```

2. **Implement the adapter**:
   ```python
   # src/searchmuse/adapters/my_adapter.py
   class MyAdapter:
       async def my_method(self, param: str) -> str:
           """Implementation."""
           return "result"
   ```

3. **Add tests**:
   ```python
   # tests/adapters/test_my_adapter.py
   import pytest
   from searchmuse.adapters.my_adapter import MyAdapter

   class TestMyAdapter:
       @pytest.mark.asyncio
       async def test_my_method(self):
           adapter = MyAdapter()
           result = await adapter.my_method("input")
           assert result == "expected"
   ```

4. **Update configuration**:
   ```yaml
   # config/default.yaml
   my_service:
     adapter: my_adapter
     param: value
   ```

5. **Document in**:
   - [Components Guide](002_components.md)
   - README in the adapter file

## Documentation

Update documentation when:

- Adding new public API
- Changing configuration options
- Adding features
- Fixing bugs with workarounds

Documentation files:
- API changes: [API Reference](004_api-reference.md)
- Configuration: [Configuration Reference](005_configuration-reference.md)
- Architecture: [Architecture Guide](001_architecture.md)
- User guide: [User Guide](../001_functional/user-guide.md)

## Related Links

- [Architecture Overview](001_architecture.md)
- [Components Guide](002_components.md)
- [Testing Strategy](007_testing-strategy.md)
- [Development Setup](006_development-setup.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Security Policy](SECURITY.md)

## Questions?

- Open an issue for questions
- Check existing issues and discussions
- Read relevant documentation
- Ask in pull request comments

---

Last updated: 2026-02-28
Maintainers: [List of maintainers]
