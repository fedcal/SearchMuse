"""Protocol definition for content extractor adapter port."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from searchmuse.domain.enums import ContentType
    from searchmuse.domain.models import ExtractedContent, ScrapedPage


@runtime_checkable
class ContentExtractorPort(Protocol):
    """Abstract port for extracting clean text from raw scraped pages.

    Implementations wrap libraries such as trafilatura or readability-lxml.
    All methods raise ContentExtractionError on failure.
    """

    def extract(self, page: ScrapedPage) -> ExtractedContent:
        """Extract structured text content from a raw scraped page.

        Args:
            page: A frozen ScrapedPage containing raw HTML and metadata.

        Returns:
            A frozen ExtractedContent with cleaned text and metadata.
        """
        ...

    def supports_content_type(self, content_type: ContentType) -> bool:
        """Return True if this extractor can process the given content type.

        Args:
            content_type: The ContentType enum value to check.

        Returns:
            True when this extractor handles the content type.
        """
        ...
