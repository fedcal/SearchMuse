# SearchMuse Documentation

Welcome to SearchMuse, an intelligent web research assistant powered by local LLMs via Ollama. This documentation covers everything from getting started to advanced architecture and deployment.

## What is SearchMuse?

SearchMuse is an open-source Python application that automates iterative web research. It uses Ollama-powered language models to craft intelligent search strategies, execute scraping with proper citation tracking, and synthesize high-quality research results. Built on hexagonal architecture principles, SearchMuse is extensible, testable, and production-ready.

**Key Features:**
- Intelligent iterative search refinement with local LLMs
- Automatic source scraping and content extraction
- Proper citation tracking with verified sources
- Hexagonal architecture for extensibility
- Async-first design for performance
- Comprehensive test coverage
- MIT License - free for personal and commercial use

## Quick Links

**New Users:**
- [Getting Started](002_technical/006_development-setup.md) - Set up SearchMuse locally
- [User Guide](001_functional/user-guide.md) - Learn how to use the application
- [Configuration Guide](002_technical/005_configuration-reference.md) - Configure for your needs

**Developers:**
- [Architecture Overview](002_technical/001_architecture.md) - Understand the design
- [Components Guide](002_technical/002_components.md) - Learn about each component
- [API Reference](002_technical/004_api-reference.md) - Domain classes and interfaces
- [Data Flow](002_technical/003_data-flow.md) - How data moves through the system
- [Development Setup](002_technical/006_development-setup.md) - Set up dev environment
- [Testing Strategy](002_technical/007_testing-strategy.md) - Write and run tests
- [Contributing Guide](002_technical/010_contributing.md) - Contribute to the project

**Operations:**
- [Deployment Guide](002_technical/008_deployment.md) - Deploy to production
- [Security Guide](002_technical/009_security.md) - Security considerations
- [Configuration Reference](002_technical/005_configuration-reference.md) - All config options

## Project Structure

```
SearchMuse/
├── docs/                           # Documentation (this directory)
│   ├── 000_index.md               # Documentation homepage
│   ├── 001_functional/            # Functional documentation
│   │   ├── 000_README.md
│   │   ├── 001_vision-and-goals.md
│   │   ├── 002_use-cases.md
│   │   ├── 003_feature-specifications.md
│   │   ├── 004_search-refinement-algorithm.md
│   │   ├── 005_source-citation.md
│   │   ├── 006_supported-websites.md
│   │   ├── 007_llm-requirements.md
│   │   ├── 008_input-output-formats.md
│   │   ├── 009_limitations.md
│   │   └── 010_roadmap.md
│   ├── 002_technical/             # Technical documentation
│   │   ├── 001_architecture.md
│   │   ├── 002_components.md
│   │   ├── 003_data-flow.md
│   │   ├── 004_api-reference.md
│   │   ├── 005_configuration-reference.md
│   │   ├── 006_development-setup.md
│   │   ├── 007_testing-strategy.md
│   │   ├── 008_deployment.md
│   │   ├── 009_security.md
│   │   └── 010_contributing.md
│   └── 003_it/                    # Italian documentation
│       └── (Italian versions of all docs)
├── src/searchmuse/                # Application source code
│   ├── domain/                    # Domain layer (business logic)
│   ├── ports/                     # Port interfaces
│   ├── adapters/                  # Adapter implementations
│   ├── application/               # Application layer
│   ├── infrastructure/            # Infrastructure layer
│   └── cli/                       # Command-line interface
├── tests/                         # Test suite
├── pyproject.toml                 # Python project configuration
└── README.md                      # Project README
```

## Technology Stack

**Core Dependencies:**
- **httpx** - Modern HTTP client for async requests
- **playwright** - Browser automation (optional, for JavaScript-heavy sites)
- **trafilatura** - Web scraping and content extraction
- **readability-lxml** - Article extraction
- **beautifulsoup4** - HTML/XML parsing
- **ollama** - Local LLM integration
- **duckduckgo-search** - Search engine integration
- **typer** - Modern CLI framework
- **rich** - Terminal formatting and UI
- **pyyaml** - Configuration file parsing
- **aiosqlite** - Async SQLite database access

**Development Tools:**
- **pytest** - Testing framework
- **pytest-asyncio** - Async test support
- **pytest-cov** - Coverage reporting
- **mypy** - Static type checking
- **ruff** - Fast Python linter and formatter
- **respx** - Mock HTTP requests in tests

## Documentation Conventions

- **Code examples** are in Python unless otherwise noted
- **File paths** are relative to the project root
- **Configuration examples** use YAML format
- **Diagrams** use Mermaid syntax
- **Cross-references** link to relevant documentation

## Italian Documentation

Documentazione in italiano disponibile in `docs/003_it/`. Per una migliore esperienza, consultare la versione localizzata.

## Getting Help

- **Questions?** Check the [FAQ](001_functional/faq.md)
- **Found a bug?** Open an issue on GitHub
- **Want to contribute?** See the [Contributing Guide](002_technical/010_contributing.md)
- **Need help?** Check [Troubleshooting](001_functional/troubleshooting.md)

## License

SearchMuse is licensed under the MIT License. See LICENSE file for details.

---

Last updated: 2026-02-28
Version: 1.0.0
[GitHub Repository](https://github.com/yourorg/searchmuse)
