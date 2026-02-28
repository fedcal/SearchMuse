# Development Setup

Questa guida spiega come configurare un ambiente di sviluppo per contribuire a SearchMuse.

## Prerequisiti

### Sistema Operativo e Runtime

- **Python**: 3.11 o superiore
- **pip**: Gestore di pacchetti Python
- **git**: Controllo versione
- **RAM**: 2 GB minimo (4 GB consigliati)
- **Spazio disco**: 5 GB minimo

### Verificare Python

```bash
python3 --version
# Output atteso: Python 3.11.x o superiore

pip3 --version
# Output atteso: pip 23.x o superiore
```

### Sistemi Linux

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install python3.11 python3.11-venv python3.11-dev

# Fedora/RHEL
sudo dnf install python3.11 python3.11-devel

# Verifica
python3.11 --version
```

### macOS

```bash
# Con Homebrew
brew install python@3.11

# Verifica
python3.11 --version
```

### Windows

- Scaricare Python 3.11+ da https://www.python.org/downloads/
- Installare selezionando "Add Python to PATH"
- Verificare: `python --version`

## Clone e Installazione

### 1. Clonare il Repository

```bash
git clone https://github.com/federicocalo/WebScraping.git
cd WebScraping
```

### 2. Creare Virtual Environment

```bash
# Linux/macOS
python3.11 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Aggiornare pip

```bash
pip install --upgrade pip setuptools wheel
```

### 4. Installare Dipendenze di Sviluppo

```bash
# Installare il package in modalità edit con dipendenze di dev
pip install -e ".[dev]"
```

Questo installa:
- Dipendenze core (httpx, playwright, typer, etc.)
- Dipendenze di test (pytest, pytest-cov, etc.)
- Dipendenze di development (black, ruff, mypy, etc.)

### 5. Post-Installazione

```bash
# Installare Playwright browsers
playwright install

# Verificare l'installazione
searchmuse --help
```

## Configurazione Ollama

### Installazione Ollama

Scaricare da https://ollama.ai

```bash
# Linux
curl https://ollama.ai/install.sh | sh

# macOS
# Scaricare il .dmg e installare

# Windows
# Scaricare il .exe e installare
```

### Avvio di Ollama

```bash
# Linux/macOS
ollama serve

# macOS (se installato via Homebrew)
brew services start ollama

# Windows
# Eseguire Ollama dall'Application Menu
```

### Scaricare un Modello

```bash
# Modello consigliato per development
ollama pull mistral

# Modelli alternativi
ollama pull neural-chat
ollama pull llama2

# Verificare i modelli disponibili
ollama list
```

### Verificare la Connessione

```bash
# Verificare che Ollama sia raggiungibile
curl http://localhost:11434/api/tags

# Output atteso:
# {"models":[{"name":"mistral:latest",...}]}
```

## Configurazione IDE

### Visual Studio Code

1. **Installare estensioni**:
   - Python (Microsoft)
   - Pylance (Microsoft)
   - Black Formatter (Microsoft)
   - Ruff (Astral)
   - pytest (Hynek Schlawack)

2. **Creare `.vscode/settings.json`**:
```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
  "python.formatting.provider": "black",
  "[python]": {
    "editor.formatOnSave": true,
    "editor.defaultFormatter": "ms-python.black-formatter",
    "editor.codeActionsOnSave": {
      "source.organizeImports": true,
      "source.fixAll": true
    }
  },
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": [
    "tests"
  ]
}
```

3. **Creare `.vscode/launch.json`**:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "SearchMuse CLI",
      "type": "python",
      "request": "launch",
      "module": "searchmuse.cli",
      "args": ["search", "--query", "python"],
      "justMyCode": true
    },
    {
      "name": "pytest",
      "type": "python",
      "request": "launch",
      "module": "pytest",
      "args": ["tests", "-v"],
      "justMyCode": false
    }
  ]
}
```

### PyCharm

1. **Impostare l'interprete Python**:
   - Andare a Settings > Project > Python Interpreter
   - Selezionare Existing Environment
   - Indicare il path del venv

2. **Abilitare Code Style**:
   - Settings > Editor > Code Style > Python
   - Selezionare "Black" come formatter

3. **Configurare i test**:
   - Settings > Tools > Python Integrated Tools
   - Selezionare pytest come test runner

## Comandi di Sviluppo Comuni

### Installazione Dipendenze

```bash
# Core dependencies
pip install httpx playwright typer pydantic pyyaml

# Dev dependencies
pip install pytest pytest-cov pytest-mock black ruff mypy

# Type checking
pip install types-PyYAML
```

### Formatting e Linting

```bash
# Format codice con Black
black searchmuse tests

# Controllare lint con Ruff
ruff check searchmuse tests

# Type checking con mypy
mypy searchmuse
```

### Esecuzione dei Test

```bash
# Tutti i test
pytest tests/

# Test specifico
pytest tests/test_domain/test_models.py

# Con coverage
pytest tests/ --cov=searchmuse --cov-report=html

# Verbose
pytest tests/ -vv

# Solo test veloce
pytest tests/ -m "not slow"
```

### Esecuzione dell'Applicazione

```bash
# Ricerca semplice
searchmuse search "Cosa è la fotosintesi?"

# Ricerca con parametri
searchmuse search --query "AI" --max-iterations 5 --language en

# Mostrare sessioni precedenti
searchmuse session list

# Mostrare sessione specifica
searchmuse session show <session_id>
```

## Struttura del Progetto

```
WebScraping/
├── searchmuse/              # Codice sorgente
│   ├── domain/             # Logica di business
│   │   ├── models.py
│   │   ├── services.py
│   │   └── exceptions.py
│   ├── ports/              # Interfacce
│   │   ├── llm_port.py
│   │   ├── search_port.py
│   │   ├── scraper_port.py
│   │   └── repository_port.py
│   ├── adapters/           # Implementazioni
│   │   ├── ollama/
│   │   ├── duckduckgo/
│   │   ├── playwright/
│   │   └── sqlite/
│   ├── application/        # Orchestrazione
│   │   └── use_cases.py
│   └── cli/                # Interfaccia CLI
│       └── commands.py
├── tests/                  # Test suite
│   ├── unit/
│   ├── integration/
│   ├── e2e/
│   └── conftest.py
├── docs/                   # Documentazione
│   ├── index.md
│   ├── technical/
│   └── it/
├── pyproject.toml          # Configurazione progetto
├── pytest.ini              # Configurazione pytest
├── .gitignore
├── LICENSE
└── README.md
```

## Playwright Setup

### Installazione Browser

```bash
# Installa automaticamente i browser supportati
playwright install

# Installa solo Chromium
playwright install chromium

# Verifica l'installazione
playwright install --with-deps
```

### Test Playwright

```bash
# Eseguire test di scraping
pytest tests/integration/test_playwright_adapter.py -v

# Debug con browser visibile
PLAYWRIGHT_HEADLESS=false pytest tests/integration/ -v
```

## Troubleshooting

### Virtual Environment non attivato

```bash
# Linux/macOS
source venv/bin/activate

# Windows
venv\Scripts\activate

# Verificare
which python  # Dovrebbe mostrare /path/to/venv/bin/python
```

### Ollama non trovato

```bash
# Verificare che Ollama sia in esecuzione
ps aux | grep ollama

# Se non è in esecuzione
ollama serve &

# Se porta è diversa, aggiornare config
export SEARCHMUSE_OLLAMA_HOST=localhost
export SEARCHMUSE_OLLAMA_PORT=11434
```

### Errori di import

```bash
# Reinstallare il package in modalità edit
pip install -e .

# Verificare i path di Python
python -c "import sys; print(sys.path)"
```

### Test falliti

```bash
# Eseguire con verbosity
pytest tests/ -vv

# Eseguire test specifico
pytest tests/test_domain/test_models.py::test_search_query_validation -vv

# Con debugging
pytest tests/ -vv --pdb
```

## Prossimi Passi

Dopo aver configurato l'ambiente di sviluppo:

1. Leggi [Contributing](./010_contributing.md) per le linee guida di contribuzione
2. Consulta [Testing Strategy](./007_testing-strategy.md) per il modello di test
3. Rivedi [Architecture](./001_architecture.md) per comprendre il design
4. Esegui i test: `pytest tests/ -v`

---

**Versione**: 1.0
**Ultimo Aggiornamento**: Febbraio 2026
**Stato**: Stabile
