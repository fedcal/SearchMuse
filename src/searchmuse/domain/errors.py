"""Exception hierarchy for SearchMuse domain errors."""


class SearchMuseError(Exception):
    """Base exception for all SearchMuse errors."""

    def __str__(self) -> str:
        return self.args[0] if self.args else "SearchMuse error occurred"


class ConfigurationError(SearchMuseError):
    """Raised when configuration is missing or invalid."""

    def __init__(self, message: str) -> None:
        super().__init__(message)

    def __str__(self) -> str:
        return f"Configuration error: {self.args[0]}"


class LLMError(SearchMuseError):
    """Base exception for LLM adapter errors."""

    def __init__(self, message: str, *, model: str, detail: str) -> None:
        super().__init__(message)
        self.model = model
        self.detail = detail

    def __str__(self) -> str:
        return f"LLM error [{self.model}]: {self.args[0]} — {self.detail}"


class LLMAuthenticationError(LLMError):
    """Raised when an LLM provider rejects the supplied API key."""

    def __str__(self) -> str:
        return (
            f"LLM authentication failed [{self.model}]: {self.args[0]} — {self.detail}"
        )


class LLMConnectionError(LLMError):
    """Raised when the LLM service cannot be reached."""

    def __str__(self) -> str:
        return f"LLM connection failed [{self.model}]: {self.args[0]} — {self.detail}"


class LLMResponseError(LLMError):
    """Raised when an LLM response is malformed or unparseable."""

    def __str__(self) -> str:
        return f"LLM bad response [{self.model}]: {self.args[0]} — {self.detail}"


class ScrapingError(SearchMuseError):
    """Base exception for scraping failures."""

    def __init__(self, message: str, *, url: str) -> None:
        super().__init__(message)
        self.url = url

    def __str__(self) -> str:
        return f"Scraping error for {self.url!r}: {self.args[0]}"


class RobotsTxtBlockedError(ScrapingError):
    """Raised when robots.txt disallows access to a URL."""

    def __str__(self) -> str:
        return f"Blocked by robots.txt: {self.url!r}"


class RequestTimeoutError(ScrapingError):
    """Raised when an HTTP request exceeds the configured timeout."""

    def __str__(self) -> str:
        return f"Request timed out for {self.url!r}: {self.args[0]}"


class ContentExtractionError(SearchMuseError):
    """Raised when text cannot be extracted from a scraped page."""

    def __init__(self, message: str, *, url: str) -> None:
        super().__init__(message)
        self.url = url

    def __str__(self) -> str:
        return f"Content extraction failed for {self.url!r}: {self.args[0]}"


class ValidationError(SearchMuseError):
    """Raised when domain input validation fails."""

    def __init__(self, message: str, *, field: str, detail: str) -> None:
        super().__init__(message)
        self.field = field
        self.detail = detail

    def __str__(self) -> str:
        return f"Validation failed on field {self.field!r}: {self.detail}"


class StorageError(SearchMuseError):
    """Raised when a persistence operation fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message)

    def __str__(self) -> str:
        return f"Storage error: {self.args[0]}"
