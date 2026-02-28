# Riferimento API

Questo documento fornisce una referenza completa di tutti i modelli di dominio, le interfacce (Protocol) e le eccezioni di SearchMuse.

## Modelli di Dominio

### SearchQuery

Rappresenta una query di ricerca fornita dall'utente.

```python
@dataclass(frozen=True)
class SearchQuery:
    """
    Una query di ricerca con parametri di configurazione.
    """
    query: str
    """La domanda o query di ricerca (obbligatorio, non vuoto)."""

    max_iterations: int = 3
    """Numero massimo di iterazioni di ricerca e raffinamento (default: 3)."""

    language: str = "it"
    """Codice lingua per i risultati (ISO 639-1, default: "it")."""

    metadata: dict[str, Any] = field(default_factory=dict)
    """Metadata aggiuntivi su questa ricerca."""

    def validate(self) -> None:
        """Valida l'integrità della query."""
        if not self.query or not self.query.strip():
            raise ValueError("query non può essere vuota")
        if self.max_iterations < 1:
            raise ValueError("max_iterations deve essere >= 1")
```

### SearchResult

Rappresenta un singolo risultato di ricerca da una fonte esterna.

```python
@dataclass(frozen=True)
class SearchResult:
    """
    Un risultato di ricerca da un motore di ricerca.
    """
    title: str
    """Titolo del risultato."""

    url: str
    """URL della risorsa."""

    snippet: str
    """Snippet testuale dal motore di ricerca."""

    source: str
    """Sorgente del risultato (es. 'duckduckgo')."""

    retrieved_at: datetime
    """Data e ora del recupero."""

    def is_valid_url(self) -> bool:
        """Verifica se l'URL è valida."""
        return self.url.startswith(("http://", "https://"))
```

### Citation

Rappresenta una citazione tracciata da una fonte specifica.

```python
@dataclass(frozen=True)
class Citation:
    """
    Una citazione con metadata di origine.
    """
    source_url: str
    """URL della fonte della citazione."""

    source_title: str
    """Titolo della fonte."""

    excerpt: str
    """Testo citato dalla fonte (max 500 caratteri)."""

    page_number: int | None = None
    """Numero di pagina (se applicabile)."""

    retrieved_at: datetime = field(default_factory=datetime.now)
    """Data e ora del recupero."""

    def to_markdown(self) -> str:
        """Formatta la citazione in Markdown."""
        return f"[{self.source_title}]({self.source_url})"
```

### IterationResult

Rappresenta i risultati di una singola iterazione.

```python
@dataclass(frozen=True)
class IterationResult:
    """
    Risultati di una iterazione di ricerca e analisi.
    """
    iteration_number: int
    """Numero dell'iterazione (1-based)."""

    refined_query: str | None
    """Query raffinata per la prossima iterazione."""

    search_results: list[SearchResult]
    """Risultati della ricerca di questa iterazione."""

    llm_analysis: str
    """Analisi generata dall'LLM."""

    citations_used: list[Citation]
    """Citations estratte in questa iterazione."""

    def has_results(self) -> bool:
        """Verifica se ci sono risultati."""
        return len(self.search_results) > 0

    def citation_count(self) -> int:
        """Ritorna il numero di citazioni."""
        return len(self.citations_used)
```

### ResearchSession

Rappresenta una sessione di ricerca completa.

```python
@dataclass(frozen=True)
class ResearchSession:
    """
    Una sessione di ricerca completa con tutte le iterazioni.
    """
    session_id: str
    """ID univoco della sessione (UUID)."""

    initial_query: SearchQuery
    """Query iniziale fornita dall'utente."""

    iterations: list[IterationResult]
    """Tutte le iterazioni eseguite."""

    final_answer: str
    """Risposta finale consolidata."""

    total_sources: int
    """Numero totale di fonti uniche utilizzate."""

    created_at: datetime
    """Timestamp creazione sessione."""

    completed_at: datetime | None = None
    """Timestamp completamento sessione."""

    def is_complete(self) -> bool:
        """Verifica se la sessione è completata."""
        return self.completed_at is not None

    def duration(self) -> timedelta | None:
        """Calcola la durata della ricerca."""
        if self.completed_at is None:
            return None
        return self.completed_at - self.created_at

    def all_citations(self) -> list[Citation]:
        """Ritorna tutte le citazioni da tutte le iterazioni."""
        return [c for it in self.iterations for c in it.citations_used]
```

## Interfacce (Protocol)

### LLMPort

Interfaccia per i modelli linguistici.

```python
class LLMPort(Protocol):
    """
    Protocollo per i modelli linguistici.
    """

    def generate(self, prompt: str, max_tokens: int = 1000) -> str:
        """
        Genera testo basato sul prompt fornito.

        Args:
            prompt: Il testo del prompt (non vuoto).
            max_tokens: Numero massimo di token da generare.

        Returns:
            Testo generato dal modello.

        Raises:
            LLMException: Se la generazione fallisce.
        """
        ...

    def summarize(
        self,
        text: str,
        max_length: int = 500,
        language: str = "it"
    ) -> str:
        """
        Riassume un testo fornito.

        Args:
            text: Testo da riassumere.
            max_length: Lunghezza massima del riassunto.
            language: Lingua del riassunto.

        Returns:
            Testo riassunto.

        Raises:
            LLMException: Se il riassunto fallisce.
        """
        ...

    def refine_query(
        self,
        current_query: str,
        context: str,
        max_length: int = 100
    ) -> str:
        """
        Affina una query basata sul contesto precedente.

        Args:
            current_query: Query da affinare.
            context: Contesto da usare per il raffinamento.
            max_length: Lunghezza massima della query raffinata.

        Returns:
            Query raffinata.

        Raises:
            LLMException: Se il raffinamento fallisce.
        """
        ...
```

### SearchEnginePort

Interfaccia per i motori di ricerca.

```python
class SearchEnginePort(Protocol):
    """
    Protocollo per i motori di ricerca.
    """

    def search(
        self,
        query: str,
        num_results: int = 10,
        language: str = "it"
    ) -> list[SearchResult]:
        """
        Esegue una ricerca e ritorna i risultati.

        Args:
            query: Query di ricerca.
            num_results: Numero di risultati da ritornare.
            language: Lingua dei risultati.

        Returns:
            Lista di SearchResult ordinata per rilevanza.

        Raises:
            SearchEngineException: Se la ricerca fallisce.
        """
        ...

    def search_with_filters(
        self,
        query: str,
        num_results: int = 10,
        language: str = "it",
        safe_search: bool = True,
        time_range: str | None = None
    ) -> list[SearchResult]:
        """
        Esegue una ricerca con filtri aggiuntivi.

        Args:
            query: Query di ricerca.
            num_results: Numero di risultati.
            language: Lingua dei risultati.
            safe_search: Abilitare safe search.
            time_range: Intervallo temporale ('1w', '1m', '1y').

        Returns:
            Lista di SearchResult filtrati.

        Raises:
            SearchEngineException: Se la ricerca fallisce.
        """
        ...
```

### WebScraperPort

Interfaccia per il web scraping.

```python
class WebScraperPort(Protocol):
    """
    Protocollo per il web scraping.
    """

    def fetch(
        self,
        url: str,
        timeout: int = 10,
        follow_redirects: bool = True
    ) -> str:
        """
        Recupera il contenuto HTML di una URL.

        Args:
            url: URL da recuperare.
            timeout: Timeout in secondi.
            follow_redirects: Seguire i redirect HTTP.

        Returns:
            Contenuto HTML della pagina.

        Raises:
            WebScraperException: Se il fetch fallisce.
        """
        ...

    def extract_text(self, html: str, remove_scripts: bool = True) -> str:
        """
        Estrae testo pulito da HTML.

        Args:
            html: HTML da processare.
            remove_scripts: Rimuovere tag script e style.

        Returns:
            Testo estratto e pulito.

        Raises:
            WebScraperException: Se l'estrazione fallisce.
        """
        ...
```

### RepositoryPort

Interfaccia per la persistenza.

```python
class RepositoryPort(Protocol):
    """
    Protocollo per la persistenza dei dati.
    """

    def save_session(self, session: ResearchSession) -> str:
        """
        Salva una sessione di ricerca.

        Args:
            session: Sessione da salvare.

        Returns:
            session_id della sessione salvata.

        Raises:
            RepositoryException: Se il salvataggio fallisce.
        """
        ...

    def get_session(self, session_id: str) -> ResearchSession | None:
        """
        Recupera una sessione di ricerca.

        Args:
            session_id: ID della sessione da recuperare.

        Returns:
            ResearchSession se trovata, None altrimenti.

        Raises:
            RepositoryException: Se il recupero fallisce.
        """
        ...

    def list_sessions(
        self,
        limit: int = 10,
        offset: int = 0
    ) -> list[ResearchSession]:
        """
        Elenca le sessioni di ricerca.

        Args:
            limit: Numero massimo di risultati.
            offset: Numero di risultati da saltare.

        Returns:
            Lista di ResearchSession ordinate per data decrescente.

        Raises:
            RepositoryException: Se l'elencazione fallisce.
        """
        ...

    def delete_session(self, session_id: str) -> bool:
        """
        Cancella una sessione di ricerca.

        Args:
            session_id: ID della sessione da cancellare.

        Returns:
            True se cancellata, False se non trovata.

        Raises:
            RepositoryException: Se la cancellazione fallisce.
        """
        ...
```

## Enumerazioni

### SearchResultSource

Enumera le possibili sorgenti di risultati.

```python
from enum import Enum

class SearchResultSource(Enum):
    """Sorgenti possibili per i risultati di ricerca."""
    DUCKDUCKGO = "duckduckgo"
    GOOGLE = "google"
    BING = "bing"
    WIKIPEDIA = "wikipedia"
```

### ErrorLevel

Livelli di severità degli errori.

```python
from enum import Enum

class ErrorLevel(Enum):
    """Livelli di severità degli errori."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
```

## Eccezioni

### SearchMuseException

Eccezione base per tutte le eccezioni di SearchMuse.

```python
class SearchMuseException(Exception):
    """
    Eccezione base per SearchMuse.
    """
    def __init__(
        self,
        message: str,
        error_code: str | None = None,
        details: dict[str, Any] | None = None
    ):
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}
```

### DomainException

Eccezione per violazioni di invarianti di dominio.

```python
class DomainException(SearchMuseException):
    """Eccezione sollevata per violazioni di dominio."""
    pass
```

### LLMException

Eccezione per errori della comunicazione con l'LLM.

```python
class LLMException(SearchMuseException):
    """Eccezione sollevata da errori di LLM."""
    pass

class LLMTimeoutException(LLMException):
    """LLM ha superato il timeout."""
    pass

class LLMConnectionException(LLMException):
    """Impossibile connettersi a Ollama."""
    pass
```

### SearchEngineException

Eccezione per errori della comunicazione con il motore di ricerca.

```python
class SearchEngineException(SearchMuseException):
    """Eccezione sollevata da errori di ricerca."""
    pass

class SearchRateLimitException(SearchEngineException):
    """Rate limit raggiunto dal motore di ricerca."""
    pass
```

### WebScraperException

Eccezione per errori del web scraping.

```python
class WebScraperException(SearchMuseException):
    """Eccezione sollevata da errori di scraping."""
    pass

class URLNotReachableException(WebScraperException):
    """URL non raggiungibile."""
    pass
```

### RepositoryException

Eccezione per errori della persistenza.

```python
class RepositoryException(SearchMuseException):
    """Eccezione sollevata da errori di repository."""
    pass

class SessionNotFoundException(RepositoryException):
    """Sessione non trovata nel repository."""
    pass
```

## Utilizzo Tipico

### Creazione di una Query

```python
from searchmuse.domain.models import SearchQuery

# Creazione semplice
query = SearchQuery(query="Come funziona la fotosintesi?")

# Con parametri personalizzati
query = SearchQuery(
    query="Ultimi sviluppi in AI",
    max_iterations=5,
    language="en",
    metadata={"user_id": "user123"}
)

# Validazione
query.validate()
```

### Handling Eccezioni

```python
from searchmuse.domain.exceptions import LLMException, SearchEngineException

try:
    results = search_engine.search("query")
except SearchEngineException as e:
    logger.error(f"Errore ricerca: {e.error_code}")
except LLMException as e:
    logger.error(f"Errore LLM: {e.details}")
```

---

**Versione**: 1.0
**Ultimo Aggiornamento**: Febbraio 2026
**Stato**: Stabile
