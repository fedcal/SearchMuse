"""Trafilatura-based content extractor with readability-lxml fallback.

Primary path: trafilatura.extract() for body text, trafilatura.extract_metadata()
for title, author, and publication date.

Fallback path (triggered when trafilatura returns None or empty text):
readability.Document distils the HTML to its main article fragment, and
BeautifulSoup strips the remaining HTML tags to plain text.

Raises ContentExtractionError when the final word count is below the
configured minimum, ensuring downstream consumers always receive
substantive text.
"""

from __future__ import annotations

import logging
import uuid
from typing import TYPE_CHECKING

import trafilatura
from bs4 import BeautifulSoup
from readability import Document  # type: ignore[import-untyped]

from searchmuse.domain.enums import ContentType
from searchmuse.domain.errors import ContentExtractionError
from searchmuse.domain.models import ExtractedContent, ScrapedPage

if TYPE_CHECKING:
    from searchmuse.infrastructure.config import ExtractionConfig

logger = logging.getLogger(__name__)

# Content types this adapter can process.
_SUPPORTED_TYPES: frozenset[ContentType] = frozenset(
    {ContentType.HTML, ContentType.PLAIN_TEXT}
)


class TrafilaturaExtractorAdapter:
    """Extracts clean article text from HTML using trafilatura and readability.

    Attributes:
        _config: Frozen extraction configuration controlling thresholds
            and extractor preference.
    """

    def __init__(self, config: ExtractionConfig) -> None:
        """Initialise the adapter with the given extraction configuration.

        Args:
            config: Frozen ExtractionConfig with min_word_count,
                max_text_length, and preferred_extractor fields.
        """
        self._config = config

    # ------------------------------------------------------------------
    # Public protocol surface
    # ------------------------------------------------------------------

    def extract(self, page: ScrapedPage) -> ExtractedContent:
        """Extract structured text content from a raw scraped page.

        Attempts trafilatura first. If that returns empty text, falls back
        to readability-lxml combined with BeautifulSoup tag stripping.

        Args:
            page: A frozen ScrapedPage containing raw HTML and metadata.

        Returns:
            A new, frozen ExtractedContent instance with cleaned text,
            title, author, date, and word count.

        Raises:
            ContentExtractionError: When the final word count is below
                config.min_word_count, indicating unusable content.
        """
        raw_html = page.raw_html

        clean_text, title, author, published_date = self._extract_via_trafilatura(raw_html)

        if not clean_text:
            logger.debug("trafilatura returned empty text for %s; trying readability", page.url)
            clean_text, title = self._extract_via_readability(raw_html, fallback_title=title)

        word_count = len(clean_text.split())

        if word_count < self._config.min_word_count:
            raise ContentExtractionError(
                f"Extracted text has {word_count} words, "
                f"below minimum of {self._config.min_word_count}",
                url=page.url,
            )

        truncated_text = clean_text[: self._config.max_text_length]

        return ExtractedContent(
            content_id=str(uuid.uuid4()),
            page_id=page.page_id,
            url=page.url,
            title=title,
            clean_text=truncated_text,
            author=author,
            published_date=published_date,
            word_count=word_count,
        )

    def supports_content_type(self, content_type: ContentType) -> bool:
        """Return True when this adapter can process the given content type.

        Args:
            content_type: The ContentType enum value to check.

        Returns:
            True for HTML and PLAIN_TEXT; False for all other types.
        """
        return content_type in _SUPPORTED_TYPES

    # ------------------------------------------------------------------
    # Private extraction helpers
    # ------------------------------------------------------------------

    def _extract_via_trafilatura(
        self, raw_html: str
    ) -> tuple[str, str, str | None, str | None]:
        """Attempt extraction with trafilatura.

        Args:
            raw_html: Full raw HTML string from the scraped page.

        Returns:
            A 4-tuple of (clean_text, title, author, published_date).
            clean_text is an empty string when trafilatura yields nothing.
            title defaults to an empty string when not found.
            author and published_date are None when not detected.
        """
        clean_text: str = trafilatura.extract(
            raw_html,
            include_comments=False,
            include_tables=True,
            output_format="txt",
        ) or ""

        metadata = trafilatura.extract_metadata(raw_html)

        title: str = ""
        author: str | None = None
        published_date: str | None = None

        if metadata is not None:
            title = metadata.title or ""
            author = metadata.author or None
            published_date = metadata.date or None

        return clean_text, title, author, published_date

    def _extract_via_readability(
        self, raw_html: str, *, fallback_title: str
    ) -> tuple[str, str]:
        """Extract body text using readability-lxml and BeautifulSoup.

        readability.Document condenses the HTML to its main article
        fragment. BeautifulSoup then strips all remaining tags, yielding
        plain text.

        Args:
            raw_html: Full raw HTML string from the scraped page.
            fallback_title: Title to use when readability cannot determine
                one (usually the value obtained from trafilatura metadata).

        Returns:
            A 2-tuple of (clean_text, title). clean_text may be empty
            when readability also finds nothing of substance.
        """
        doc = Document(raw_html)

        title: str = doc.title() or fallback_title

        article_html: str = doc.summary(html_partial=True)
        soup = BeautifulSoup(article_html, "html.parser")
        clean_text: str = soup.get_text(separator=" ", strip=True)

        return clean_text, title
