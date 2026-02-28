"""Domain layer: models, enums, errors, and validators."""

from searchmuse.domain.enums import ContentType, RelevanceScore, SearchPhase, SourceStatus
from searchmuse.domain.errors import (
    ConfigurationError,
    ContentExtractionError,
    LLMConnectionError,
    LLMError,
    LLMResponseError,
    RequestTimeoutError,
    RobotsTxtBlockedError,
    ScrapingError,
    SearchMuseError,
    StorageError,
    ValidationError,
)
from searchmuse.domain.models import (
    Citation,
    ExtractedContent,
    ScrapedPage,
    SearchHit,
    SearchIteration,
    SearchQuery,
    SearchResult,
    SearchState,
    SearchStrategy,
    Source,
)

__all__ = [
    "Citation",
    "ConfigurationError",
    "ContentExtractionError",
    # Enums
    "ContentType",
    "ExtractedContent",
    "LLMConnectionError",
    "LLMError",
    "LLMResponseError",
    "RelevanceScore",
    "RequestTimeoutError",
    "RobotsTxtBlockedError",
    "ScrapedPage",
    "ScrapingError",
    "SearchHit",
    "SearchIteration",
    # Errors
    "SearchMuseError",
    "SearchPhase",
    # Models
    "SearchQuery",
    "SearchResult",
    "SearchState",
    "SearchStrategy",
    "Source",
    "SourceStatus",
    "StorageError",
    "ValidationError",
]
