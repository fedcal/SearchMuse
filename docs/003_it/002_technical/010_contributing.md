# Contribuire al Progetto

Grazie per l'interesse nel contribuire a SearchMuse! Questa guida descrive come contribuire al progetto in modo efficace.

## Code of Conduct

SearchMuse è impegnato nel mantenere una comunità accogliente e inclusiva. Tutti i contributori devono:

- Essere rispettosi verso gli altri
- Accettare critiche costruttive
- Focalizzarsi su ciò che è meglio per la comunità
- Segnalare comportamenti inaccettabili agli autori del progetto

## Come Contribuire

### Segnalare Bug

Se trovi un bug:

1. **Controlla i problemi esistenti**: Cerca se il bug è già stato segnalato
2. **Crea un nuovo Issue** con:
   - Titolo descrittivo
   - Descrizione dettagliata del problema
   - Passi per riprodurre
   - Comportamento atteso vs. effettivo
   - Ambiente (OS, versione Python, etc.)
   - Log di errore (se disponibili)

**Template di Bug Report**:
```
## Descrizione
Descrivi il bug in una o due frasi.

## Come riprodurre
Passi dettagliati per riprodurre il comportamento:
1. ...
2. ...

## Comportamento atteso
Cosa dovrebbe accadere?

## Comportamento effettivo
Cosa accade invece?

## Ambiente
- OS: [es. Ubuntu 22.04]
- Python: [es. 3.11.2]
- SearchMuse: [es. 1.0.0]

## Log di errore
```
```
<error log here>
```
```

### Richiedere Funzionalità

Per richiedere una nuova funzionalità:

1. **Usa il template di Discussion**
2. Descrivi il use case
3. Spiega perché è utile
4. Fornisci esempi di utilizzo

**Template di Richiesta Funzionalità**:
```
## Descrizione
Descrivi la funzionalità desiderata.

## Caso d'uso
Quale problema risolverebbe?

## Esempi
Come verrebbe utilizzata?

## Alternativeese già state considerate?
```

### Contribuire Codice

#### 1. Fork il Repository

```bash
# Clona il tuo fork
git clone https://github.com/YOUR_USERNAME/WebScraping.git
cd WebScraping

# Aggiungi upstream per mantenersi sincronizzati
git remote add upstream https://github.com/federicocalo/WebScraping.git
```

#### 2. Crea un Branch

```bash
# Aggiorna dal main
git fetch upstream
git rebase upstream/main

# Crea un branch feature
git checkout -b feature/nome-della-feature
```

#### 3. Sviluppa la Funzionalità

Segui questi principi:

- **TDD**: Scrivi test prima del codice
- **Clean Code**: Segui le linee guida di stile
- **Commits atomici**: Commit piccoli e significativi
- **Documentazione**: Documenta il codice e i cambiamenti

#### 4. Esegui i Test Localmente

```bash
# Installa dipendenze di test
pip install -e ".[dev]"

# Esegui tutti i test
pytest tests/ -v

# Esegui con coverage
pytest tests/ --cov=searchmuse --cov-report=html

# Verifica lo stile del codice
black searchmuse tests/
ruff check searchmuse tests/

# Type checking
mypy searchmuse
```

#### 5. Commit dei Cambiamenti

Usa il formato Conventional Commits:

```
<type>: <description>

<optional body>
<optional footer>
```

**Tipi di Commit**:
- `feat`: Nuova funzionalità
- `fix`: Correzione di bug
- `docs`: Cambiamenti alla documentazione
- `style`: Formatting, missing semicolons, etc.
- `refactor`: Refactoring del codice
- `perf`: Miglioramenti di performance
- `test`: Aggiunta o modifica di test
- `chore`: Cambiamenti di configurazione, dipendenze, etc.

**Esempi**:
```bash
git commit -m "feat: add iterative query refinement"
git commit -m "fix: handle timeout in ollama adapter

- Add retry logic with exponential backoff
- Log timeout errors for debugging
- Close #123"

git commit -m "docs: update api reference for SearchQuery"
```

#### 6. Aggiorna la Documentazione

Se il tuo cambiamento riguarda l'API pubblica:

- Aggiorna `/docs/technical/api-reference.md`
- Aggiorna `/docs/it/technical/api-reference.md`
- Aggiorna i docstring Python nel codice

#### 7. Crea una Pull Request

```bash
# Push il tuo branch
git push origin feature/nome-della-feature
```

**Template di PR**:
```markdown
## Descrizione
Descrivi brevemente i cambiamenti.

## Tipo di Cambiamento
- [ ] Bug fix
- [ ] Nuova funzionalità
- [ ] Breaking change
- [ ] Cambiamento della documentazione

## Cambiamenti
- Punto 1
- Punto 2

## Testing
Descrivi come hai testato i cambiamenti:
- [ ] Ho eseguito tutti i test
- [ ] Ho aggiunto nuovi test
- [ ] Coverage >= 80%

## Checklist
- [ ] Ho letto il CONTRIBUTING.md
- [ ] Ho aggiornato la documentazione
- [ ] Ho aggiunto test
- [ ] I test passano localmente
- [ ] Il codice segue lo stile del progetto
```

### Estensioni e Plugin

SearchMuse supporta un sistema di plugin per nuovi adapter.

#### Creare un Nuovo Adapter

1. **Definire il Port** (se non esiste):
```python
# In searchmuse/ports/my_port.py
from typing import Protocol

class MyPort(Protocol):
    def do_something(self, param: str) -> str:
        """Docstring explaining the method."""
        ...
```

2. **Implementare l'Adapter**:
```python
# In searchmuse/adapters/my_adapter.py
from searchmuse.ports.my_port import MyPort

class MyAdapter:
    def __init__(self, config: dict):
        self.config = config

    def do_something(self, param: str) -> str:
        # Implementazione
        return result
```

3. **Aggiungere Test**:
```python
# In tests/unit/adapters/test_my_adapter.py
def test_my_adapter_does_something():
    adapter = MyAdapter({"key": "value"})
    result = adapter.do_something("input")
    assert result == "expected"
```

4. **Documentare**:
   - Aggiungi sezione in `/docs/technical/components.md`
   - Aggiungi configurazione in `/docs/technical/configuration-reference.md`

#### Esempio: Aggiungere Support per Claude LLM

```python
# ports/llm_port.py già esiste, implementa il protocol

# adapters/claude/claude_adapter.py
from anthropic import Anthropic
from searchmuse.ports.llm_port import LLMPort

class ClaudeLLMAdapter:
    def __init__(self, api_key: str, model: str = "claude-3-sonnet"):
        self.client = Anthropic(api_key=api_key)
        self.model = model

    def generate(self, prompt: str, max_tokens: int = 1000) -> str:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text

    def summarize(self, text: str, max_length: int = 500) -> str:
        prompt = f"Summarize in {max_length} characters: {text}"
        return self.generate(prompt, max_tokens=200)

    def refine_query(self, current_query: str, context: str) -> str:
        prompt = f"Refine this query based on context:\nQuery: {current_query}\nContext: {context}"
        return self.generate(prompt, max_tokens=100)
```

## Linee Guida di Stile

### Python Style Guide

SearchMuse segue PEP 8 con strumenti automatici:

```bash
# Formatta con Black
black searchmuse/

# Linting con Ruff
ruff check searchmuse/

# Type checking con mypy
mypy searchmuse/
```

### Convenzioni di Naming

```python
# Classi: PascalCase
class SearchQuery:
    pass

# Funzioni/metodi: snake_case
def search_documents():
    pass

# Costanti: UPPER_SNAKE_CASE
MAX_ITERATIONS = 3
DEFAULT_LANGUAGE = "it"

# Parametri privati: _leading_underscore
def _internal_function():
    pass
```

### Docstring Style

Usa Google-style docstrings:

```python
def search(
    self,
    query: str,
    num_results: int = 10
) -> list[SearchResult]:
    """Esegue una ricerca e ritorna i risultati.

    Args:
        query: La query di ricerca (non vuota).
        num_results: Numero di risultati da ritornare (default: 10).

    Returns:
        Una lista di SearchResult ordinata per rilevanza.

    Raises:
        ValueError: Se query è vuota.
        SearchEngineException: Se la ricerca fallisce.

    Examples:
        >>> results = search("python")
        >>> len(results) > 0
        True
    """
```

## Review di Pull Request

Tutti i PR sono sottoposti a review per:

1. **Qualità del codice**: Segue lo stile del progetto?
2. **Test**: Ci sono test per i cambiamenti?
3. **Documentazione**: È documentato?
4. **Architettura**: Segue i principi dell'architettura esagonale?
5. **Performance**: Ci sono regressioni di performance?

I reviewer possono richiedere cambiamenti. Rispondi con civiltà e costruttività!

## Processo di Release

Le release seguono Semantic Versioning:

- **Major (X.0.0)**: Breaking changes
- **Minor (0.X.0)**: Nuove funzionalità (backwards compatible)
- **Patch (0.0.X)**: Bug fixes

## Domande?

Se hai domande:

- Apri una Discussion su GitHub
- Contatta i maintainer
- Leggi la documentazione

## Riconoscimenti

I contributori vengono riconosciuti nel file `CONTRIBUTORS.md`.

---

**Versione**: 1.0
**Ultimo Aggiornamento**: Febbraio 2026
**Stato**: Stabile
