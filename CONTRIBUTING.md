# Contributing to SearchMuse

Thank you for your interest in contributing! This file is the entry point —
the full contributor guide lives in the project documentation.

- **Full guide**: [docs/002_technical/010_contributing.md](docs/002_technical/010_contributing.md)
- **Guida in italiano**: [docs/003_it/002_technical/010_contributing.md](docs/003_it/002_technical/010_contributing.md)
- **Development setup**: [docs/002_technical/006_development-setup.md](docs/002_technical/006_development-setup.md)
- **Testing strategy**: [docs/002_technical/007_testing-strategy.md](docs/002_technical/007_testing-strategy.md)

## Quick start for contributors

1. Fork the repository and create a feature branch from `master`.
2. Install the dev environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -e ".[dev,docs]"
   ```
3. Run the quality gates locally before opening a PR:
   ```bash
   ruff check src/ tests/
   mypy src/searchmuse/
   pytest tests/ -v --cov
   mkdocs build --strict
   ```
4. Open a Pull Request against `master`. CI will run lint, type-check, tests
   and a strict docs build automatically.

## Reporting issues

Please use [GitHub Issues](https://github.com/fedcal/SearchMuse/issues) and
include reproduction steps, expected vs. actual behaviour, and your
environment (OS, Python version, LLM provider).
