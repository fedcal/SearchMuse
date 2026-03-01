# :material-home: SearchMuse

**Intelligent web research powered by local LLMs.**

SearchMuse is a CLI tool that performs iterative web research using LLM-powered search refinement and transparent source citation. It combines DuckDuckGo search, web scraping, content extraction, and LLM synthesis to produce well-cited answers to research queries.

## Features

- **Iterative search refinement** — LLM generates search strategies, assesses coverage, and refines until sufficient
- **Multi-provider LLM support** — Ollama (local), Claude, OpenAI, Gemini
- **Transparent citations** — Every claim is backed by numbered sources with URLs
- **Interactive REPL** — Chat-like terminal interface with Rich formatting
- **Hexagonal architecture** — Clean separation of ports and adapters
- **Fully typed** — Strict MyPy compliance with PEP 561 marker

## Quick Start

```bash
# Install
pip install searchmuse

# Start Ollama (if using local LLM)
ollama serve

# Pull a model
searchmuse ollama pull mistral

# Interactive mode
searchmuse

# Single query
searchmuse search "What are the latest developments in quantum computing?"
```

## Documentation

- [Functional Specifications](001_functional/000_README.md)
- [Technical Documentation](002_technical/001_architecture.md)
- [Documentazione Italiana](003_it/000_index.md)
