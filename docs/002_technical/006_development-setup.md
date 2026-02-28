# SearchMuse Development Setup

Complete guide to setting up SearchMuse for local development, including prerequisites, installation, Ollama setup, and IDE configuration.

## Prerequisites

Before setting up SearchMuse, ensure you have:

- **Python 3.11 or later** (Python 3.12+ recommended)
  - Check version: `python --version`
  - Install: https://www.python.org/downloads/

- **Git** (for cloning the repository)
  - Check installation: `git --version`
  - Install: https://git-scm.com/

- **Ollama** (for local LLM support)
  - Download: https://ollama.ai/
  - Install and start the Ollama daemon
  - Verify: `ollama list` or visit http://localhost:11434

- **pip** (Python package manager)
  - Usually included with Python 3.4+
  - Check: `pip --version`

- **4GB RAM minimum** (for Ollama models)
  - 8GB+ recommended for comfortable development

- **2GB disk space** for Ollama models and dependencies

## Step 1: Clone Repository

```bash
# Clone the repository
git clone https://github.com/yourorg/searchmuse.git
cd searchmuse

# Or fork and clone your fork
git clone https://github.com/yourusername/searchmuse.git
cd searchmuse
```

## Step 2: Create Virtual Environment

Create an isolated Python environment to avoid conflicts:

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate

# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# On Windows (Command Prompt):
venv\Scripts\activate.bat

# Verify activation (should show "venv" prefix in prompt)
which python  # Linux/macOS
where python  # Windows
```

## Step 3: Install Dependencies

Install SearchMuse in editable mode with development dependencies:

```bash
# Upgrade pip (recommended)
pip install --upgrade pip setuptools wheel

# Install SearchMuse and dev dependencies
pip install -e ".[dev]"

# Verify installation
searchmuse --version
```

**What this installs:**

- **Core dependencies**: httpx, playwright, trafilatura, ollama, typer, rich, pyyaml, aiosqlite
- **Dev dependencies**: pytest, pytest-asyncio, pytest-cov, mypy, ruff, respx
- **Editable mode**: Changes to source code are immediately reflected without reinstalling

## Step 4: Install Playwright Browsers

If using Playwright for JavaScript-heavy sites:

```bash
# Download and install browsers (one-time setup)
playwright install

# Or install specific browser
playwright install chromium
```

**Supported browsers:**
- chromium (default, ~300MB)
- firefox (~200MB)
- webkit (~150MB)

## Step 5: Set Up Ollama

### Install Ollama

1. Download from https://ollama.ai/
2. Run installer for your OS
3. Restart terminal

### Start Ollama Daemon

```bash
# Start Ollama service (runs in background)
ollama serve

# Or on macOS (if installed via Homebrew):
brew services start ollama

# Verify service is running
curl http://localhost:11434/api/tags
```

### Pull a Model

```bash
# Pull default model (Mistral 7B - recommended for CPU)
ollama pull mistral

# Or other models:
ollama pull neural-chat      # Conversation-optimized
ollama pull llama2          # Larger, higher quality
ollama pull mixtral         # Very high quality (requires 32GB+ RAM)

# List installed models
ollama list
```

**Model Selection Guide:**

| Model | Size | Speed | Quality | RAM | Notes |
|-------|------|-------|---------|-----|-------|
| mistral | 7B | Fast | Good | 4GB | Recommended for CPU |
| neural-chat | 7B | Fast | Good | 4GB | Better conversation |
| llama2 | 7B | Medium | Good | 4GB | General purpose |
| llama2 | 13B | Slow | Better | 8GB | Larger variant |
| mixtral | 8x7B | Medium | Excellent | 32GB | Expert mixture |

### Verify Ollama Connection

```bash
# Test connection in Python
python -c "
from ollama import Client
client = Client(host='http://localhost:11434')
response = client.generate(model='mistral', prompt='test', stream=False)
print('Ollama connection successful!')
"
```

## Step 6: Create Configuration File

Create a local configuration file for development:

```bash
# Copy default configuration
cp config/default.yaml config/development.yaml

# Edit for your setup (optional)
# nano config/development.yaml
```

**Example development configuration:**

```yaml
# config/development.yaml
llm:
  provider: ollama
  model: mistral
  ollama:
    base_url: http://localhost:11434

search:
  engine: duckduckgo
  results_per_query: 10

repository:
  type: sqlite
  sqlite:
    path: ./data/searchmuse_dev.db

logging:
  level: DEBUG
  file: ./logs/development.log
```

## Step 7: Verify Installation

Test that everything works:

```bash
# Run help command
searchmuse --help

# Run a simple research
searchmuse --config config/development.yaml research "What is Python?"
```

Expected output:
```
Research Results: What is Python?

Summary
-------
Python is a high-level programming language...

Sources (8 found)
-----------------
1. [Python.org - Official Python Website](https://www.python.org/)
   ...
```

## IDE Setup

### Visual Studio Code

Install extensions for better development experience:

```bash
# Install VS Code (https://code.visualstudio.com/)

# Recommended extensions:
# - Python (ms-python.python)
# - Pylance (ms-python.vscode-pylance) - type checking
# - Black Formatter (ms-python.black-formatter)
# - Ruff (charliermarsh.ruff)
# - Pytest (littlefoxteam.vscode-python-pytest)
```

**VS Code Settings (`.vscode/settings.json`):**

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": "explicit"
    }
  },
  "python.linting.ruffEnabled": true,
  "python.linting.ruffArgs": ["--line-length=100"],
  "python.testing.pytestEnabled": true,
  "python.testing.pytestPath": "${workspaceFolder}/venv/bin/pytest"
}
```

### PyCharm

Configuration steps:

1. Open project in PyCharm
2. Configure interpreter:
   - Settings → Project → Python Interpreter
   - Add Interpreter → Add Local Interpreter
   - Select `./venv/bin/python`
3. Enable pytest:
   - Settings → Tools → Python Integrated Tools
   - Default test runner: pytest
4. Configure code style:
   - Settings → Editor → Code Style
   - Line length: 100
   - Use trailing comma: Yes

### Vim/Neovim

Install language server and linter plugins:

```bash
# Using vim-plug:
Plug 'neovim/nvim-lspconfig'
Plug 'psf/black'
Plug 'charliermarsh/ruff'
Plug 'dense-analysis/ale'
```

## Running Tests

Execute the test suite:

```bash
# Run all tests with coverage
pytest --cov=searchmuse --cov-report=html

# Run specific test file
pytest tests/domain/test_search_query.py

# Run tests matching pattern
pytest tests/ -k "test_scraper"

# Run with verbose output
pytest -v tests/

# Run specific test class
pytest tests/domain/test_search_query.py::TestSearchQuery

# Run with detailed output on failure
pytest --tb=long tests/
```

See [Testing Strategy](007_testing-strategy.md) for comprehensive testing guide.

## Code Quality Tools

### Type Checking

```bash
# Run mypy for type checking (strict mode)
mypy src/ tests/

# Or with configuration:
mypy --config-file pyproject.toml src/
```

### Linting

```bash
# Check code with ruff
ruff check src/ tests/

# Auto-fix issues
ruff check --fix src/ tests/

# Format code (uses ruff as formatter)
ruff format src/ tests/
```

### Code Coverage

```bash
# Run tests with coverage report
pytest --cov=searchmuse --cov-report=html tests/

# View report (opens in browser)
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

Target: **80%+ coverage**

## Common Development Tasks

### Running a Single Feature

```bash
# Research a topic locally
searchmuse research "machine learning basics" \
  --config config/development.yaml \
  --max-iterations 2
```

### Adding a New Adapter

See [Contributing Guide](010_contributing.md) for plugin architecture.

### Testing External Services

```bash
# Test Ollama connection
python -c "
from searchmuse.adapters.ollama_llm import OllamaLLM
from searchmuse.domain import SearchQuery

llm = OllamaLLM(base_url='http://localhost:11434', model='mistral')
result = asyncio.run(llm.generate_strategy(
    SearchQuery(text='test'),
    [],
    0
))
print(result)
"

# Test DuckDuckGo search
python -c "
from searchmuse.adapters.duckduckgo_search import DuckDuckGoSearch

search = DuckDuckGoSearch()
results = asyncio.run(search.search('python programming', max_results=5))
for r in results:
    print(f'{r.title}: {r.url}')
"
```

### Database Management

```bash
# Reset database (delete and recreate)
rm -f data/searchmuse_dev.db
sqlite3 data/searchmuse_dev.db < schema.sql

# View database contents
sqlite3 data/searchmuse_dev.db
> SELECT count(*) FROM sources;
> .schema sources
```

## Troubleshooting

### "No module named 'searchmuse'"

```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall in editable mode
pip install -e ".[dev]"
```

### "Ollama connection refused"

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama (if not running)
ollama serve

# Check if model is installed
ollama list
ollama pull mistral
```

### "ModuleNotFoundError: No module named 'playwright'"

```bash
# Install playwright and browsers
pip install playwright
playwright install chromium
```

### Type checking errors despite correct code

```bash
# Update mypy
pip install --upgrade mypy

# Clear cache
mypy --no-incremental src/
```

### Tests hang or timeout

```bash
# Run with verbose output to see which test hangs
pytest -v tests/

# Increase timeout
pytest --timeout=30 tests/

# Run specific test with debugging
pytest -s tests/path/to/test.py::test_name
```

## Next Steps

1. Read the [Architecture Guide](001_architecture.md) to understand the codebase
2. Review [Testing Strategy](007_testing-strategy.md) before writing code
3. Check [Contributing Guide](010_contributing.md) for coding standards
4. Look at existing tests for examples

## Related Documentation

- [Testing Strategy](007_testing-strategy.md) - Writing and running tests
- [Contributing Guide](010_contributing.md) - Code standards and PR workflow
- [Configuration Reference](005_configuration-reference.md) - Configuration options
- [Architecture Overview](001_architecture.md) - System design

---

Last updated: 2026-02-28
