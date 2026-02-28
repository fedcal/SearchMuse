"""Domain enumerations for SearchMuse."""

from enum import StrEnum


class SearchPhase(StrEnum):
    """Represents the current phase of a search session."""

    INITIALIZING = "initializing"
    STRATEGIZING = "strategizing"
    SCRAPING = "scraping"
    EXTRACTING = "extracting"
    ASSESSING = "assessing"
    SYNTHESIZING = "synthesizing"
    COMPLETE = "complete"
    FAILED = "failed"


class ContentType(StrEnum):
    """MIME content type categories for scraped pages."""

    HTML = "html"
    PDF = "pdf"
    PLAIN_TEXT = "plain_text"
    JSON = "json"


class RelevanceScore(StrEnum):
    """LLM-assigned relevance of a source to the search query."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    IRRELEVANT = "irrelevant"


class SourceStatus(StrEnum):
    """Lifecycle status of a discovered source."""

    PENDING = "pending"
    SCRAPED = "scraped"
    EXTRACTED = "extracted"
    ASSESSED = "assessed"
    CITED = "cited"
    FAILED = "failed"
