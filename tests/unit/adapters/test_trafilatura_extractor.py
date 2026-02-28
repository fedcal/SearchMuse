"""Unit tests for TrafilaturaExtractorAdapter.

All external library calls (trafilatura, readability, BeautifulSoup) are
patched so tests run without network access or real HTML parsing.

Tests cover:
- Successful extraction via trafilatura primary path
- Readability fallback when trafilatura returns None
- ContentExtractionError when final word count is below min_word_count
- supports_content_type returns True for HTML and PLAIN_TEXT, False for PDF
- ExtractedContent fields are populated correctly
- Text truncation respects max_text_length
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest

from searchmuse.adapters.extractors.trafilatura_extractor import TrafilaturaExtractorAdapter
from searchmuse.domain.enums import ContentType
from searchmuse.domain.errors import ContentExtractionError
from searchmuse.domain.models import ExtractedContent, ScrapedPage
from searchmuse.infrastructure.config import ExtractionConfig

# ---------------------------------------------------------------------------
# Shared test constants
# ---------------------------------------------------------------------------

_MIN_WORD_COUNT: int = 50
_MAX_TEXT_LENGTH: int = 8000

_EXTRACTION_CONFIG = ExtractionConfig(
    min_word_count=_MIN_WORD_COUNT,
    max_text_length=_MAX_TEXT_LENGTH,
    preferred_extractor="trafilatura",
)

_LONG_TEXT: str = " ".join(["word"] * (_MIN_WORD_COUNT + 10))  # 60 words — above threshold
_SHORT_TEXT: str = " ".join(["word"] * (_MIN_WORD_COUNT - 1))  # 49 words — below threshold


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def config() -> ExtractionConfig:
    """Return the standard ExtractionConfig used across tests."""
    return _EXTRACTION_CONFIG


@pytest.fixture()
def adapter(config: ExtractionConfig) -> TrafilaturaExtractorAdapter:
    """Return a configured TrafilaturaExtractorAdapter."""
    return TrafilaturaExtractorAdapter(config)


@pytest.fixture()
def sample_page() -> ScrapedPage:
    """Return a minimal frozen ScrapedPage with HTML content."""
    return ScrapedPage(
        page_id="page-001",
        url="https://example.com/article",
        raw_html="<html><body><p>placeholder</p></body></html>",
        http_status=200,
        content_type=ContentType.HTML,
        scraped_at=datetime.now(UTC),
        scraper_used="httpx",
    )


def _make_metadata(
    *,
    title: str = "Test Title",
    author: str | None = "Test Author",
    date: str | None = "2024-01-15",
) -> MagicMock:
    """Return a MagicMock that mimics a trafilatura metadata object."""
    meta = MagicMock()
    meta.title = title
    meta.author = author
    meta.date = date
    return meta


# ---------------------------------------------------------------------------
# Successful extraction — trafilatura primary path
# ---------------------------------------------------------------------------


class TestSuccessfulExtraction:
    """Tests for the happy path where trafilatura returns substantive text."""

    def test_returns_extracted_content_instance(
        self, adapter: TrafilaturaExtractorAdapter, sample_page: ScrapedPage
    ) -> None:
        """extract() must return an ExtractedContent dataclass."""
        meta = _make_metadata()
        with (
            patch("trafilatura.extract", return_value=_LONG_TEXT),
            patch("trafilatura.extract_metadata", return_value=meta),
        ):
            result = adapter.extract(sample_page)

        assert isinstance(result, ExtractedContent)

    def test_clean_text_matches_trafilatura_output(
        self, adapter: TrafilaturaExtractorAdapter, sample_page: ScrapedPage
    ) -> None:
        """clean_text should equal the text returned by trafilatura.extract."""
        meta = _make_metadata()
        with (
            patch("trafilatura.extract", return_value=_LONG_TEXT),
            patch("trafilatura.extract_metadata", return_value=meta),
        ):
            result = adapter.extract(sample_page)

        assert result.clean_text == _LONG_TEXT

    def test_metadata_fields_populated_from_trafilatura(
        self, adapter: TrafilaturaExtractorAdapter, sample_page: ScrapedPage
    ) -> None:
        """title, author, and published_date come from trafilatura metadata."""
        meta = _make_metadata(title="Article Title", author="Jane Doe", date="2024-06-01")
        with (
            patch("trafilatura.extract", return_value=_LONG_TEXT),
            patch("trafilatura.extract_metadata", return_value=meta),
        ):
            result = adapter.extract(sample_page)

        assert result.title == "Article Title"
        assert result.author == "Jane Doe"
        assert result.published_date == "2024-06-01"

    def test_word_count_reflects_full_text(
        self, adapter: TrafilaturaExtractorAdapter, sample_page: ScrapedPage
    ) -> None:
        """word_count should equal the number of whitespace-separated tokens."""
        meta = _make_metadata()
        with (
            patch("trafilatura.extract", return_value=_LONG_TEXT),
            patch("trafilatura.extract_metadata", return_value=meta),
        ):
            result = adapter.extract(sample_page)

        assert result.word_count == len(_LONG_TEXT.split())

    def test_url_and_page_id_forwarded(
        self, adapter: TrafilaturaExtractorAdapter, sample_page: ScrapedPage
    ) -> None:
        """url and page_id are copied from the ScrapedPage."""
        meta = _make_metadata()
        with (
            patch("trafilatura.extract", return_value=_LONG_TEXT),
            patch("trafilatura.extract_metadata", return_value=meta),
        ):
            result = adapter.extract(sample_page)

        assert result.url == sample_page.url
        assert result.page_id == sample_page.page_id

    def test_text_truncated_to_max_text_length(
        self, adapter: TrafilaturaExtractorAdapter, sample_page: ScrapedPage
    ) -> None:
        """clean_text must not exceed config.max_text_length characters."""
        long_text = "word " * 2000  # well over 8000 characters
        meta = _make_metadata()
        with (
            patch("trafilatura.extract", return_value=long_text),
            patch("trafilatura.extract_metadata", return_value=meta),
        ):
            result = adapter.extract(sample_page)

        assert len(result.clean_text) <= _MAX_TEXT_LENGTH

    def test_none_metadata_produces_empty_title_and_none_fields(
        self, adapter: TrafilaturaExtractorAdapter, sample_page: ScrapedPage
    ) -> None:
        """When trafilatura.extract_metadata returns None all meta fields default."""
        with (
            patch("trafilatura.extract", return_value=_LONG_TEXT),
            patch("trafilatura.extract_metadata", return_value=None),
        ):
            result = adapter.extract(sample_page)

        assert result.title == ""
        assert result.author is None
        assert result.published_date is None


# ---------------------------------------------------------------------------
# Readability fallback path
# ---------------------------------------------------------------------------


class TestReadabilityFallback:
    """Tests for the secondary readability-lxml path."""

    def test_falls_back_when_trafilatura_returns_none(
        self, adapter: TrafilaturaExtractorAdapter, sample_page: ScrapedPage
    ) -> None:
        """When trafilatura.extract returns None, readability text is used."""
        fallback_text = " ".join(["fallback"] * (_MIN_WORD_COUNT + 5))

        mock_doc = MagicMock()
        mock_doc.title.return_value = "Readability Title"
        mock_doc.summary.return_value = f"<p>{fallback_text}</p>"

        mock_soup = MagicMock()
        mock_soup.get_text.return_value = fallback_text

        with (
            patch("trafilatura.extract", return_value=None),
            patch("trafilatura.extract_metadata", return_value=None),
            patch(
                "searchmuse.adapters.extractors.trafilatura_extractor.Document",
                return_value=mock_doc,
            ),
            patch(
                "searchmuse.adapters.extractors.trafilatura_extractor.BeautifulSoup",
                return_value=mock_soup,
            ),
        ):
            result = adapter.extract(sample_page)

        assert result.clean_text == fallback_text

    def test_falls_back_when_trafilatura_returns_empty_string(
        self, adapter: TrafilaturaExtractorAdapter, sample_page: ScrapedPage
    ) -> None:
        """An empty string from trafilatura also triggers the readability path."""
        fallback_text = " ".join(["fallback"] * (_MIN_WORD_COUNT + 5))

        mock_doc = MagicMock()
        mock_doc.title.return_value = "Readability Title"
        mock_doc.summary.return_value = f"<p>{fallback_text}</p>"

        mock_soup = MagicMock()
        mock_soup.get_text.return_value = fallback_text

        with (
            patch("trafilatura.extract", return_value=""),
            patch("trafilatura.extract_metadata", return_value=None),
            patch(
                "searchmuse.adapters.extractors.trafilatura_extractor.Document",
                return_value=mock_doc,
            ),
            patch(
                "searchmuse.adapters.extractors.trafilatura_extractor.BeautifulSoup",
                return_value=mock_soup,
            ),
        ):
            result = adapter.extract(sample_page)

        assert result.clean_text == fallback_text

    def test_readability_title_used_when_trafilatura_metadata_is_none(
        self, adapter: TrafilaturaExtractorAdapter, sample_page: ScrapedPage
    ) -> None:
        """When trafilatura yields no metadata, title comes from readability."""
        fallback_text = " ".join(["word"] * (_MIN_WORD_COUNT + 2))

        mock_doc = MagicMock()
        mock_doc.title.return_value = "Readability Title"
        mock_doc.summary.return_value = f"<p>{fallback_text}</p>"

        mock_soup = MagicMock()
        mock_soup.get_text.return_value = fallback_text

        with (
            patch("trafilatura.extract", return_value=None),
            patch("trafilatura.extract_metadata", return_value=None),
            patch(
                "searchmuse.adapters.extractors.trafilatura_extractor.Document",
                return_value=mock_doc,
            ),
            patch(
                "searchmuse.adapters.extractors.trafilatura_extractor.BeautifulSoup",
                return_value=mock_soup,
            ),
        ):
            result = adapter.extract(sample_page)

        assert result.title == "Readability Title"


# ---------------------------------------------------------------------------
# ContentExtractionError on low word count
# ---------------------------------------------------------------------------


class TestContentExtractionError:
    """Tests for the word-count threshold guard."""

    def test_raises_when_trafilatura_text_is_below_min_word_count(
        self, adapter: TrafilaturaExtractorAdapter, sample_page: ScrapedPage
    ) -> None:
        """ContentExtractionError must be raised when word count < min_word_count."""
        meta = _make_metadata()
        with (
            patch("trafilatura.extract", return_value=_SHORT_TEXT),
            patch("trafilatura.extract_metadata", return_value=meta),
            pytest.raises(ContentExtractionError),
        ):
            adapter.extract(sample_page)

    def test_error_url_matches_page_url(
        self, adapter: TrafilaturaExtractorAdapter, sample_page: ScrapedPage
    ) -> None:
        """ContentExtractionError.url must reference the originating page URL."""
        meta = _make_metadata()
        exc_info: pytest.ExceptionInfo[ContentExtractionError]
        with (
            patch("trafilatura.extract", return_value=_SHORT_TEXT),
            patch("trafilatura.extract_metadata", return_value=meta),
            pytest.raises(ContentExtractionError) as exc_info,
        ):
            adapter.extract(sample_page)

        assert exc_info.value.url == sample_page.url

    def test_raises_when_readability_fallback_also_below_threshold(
        self, adapter: TrafilaturaExtractorAdapter, sample_page: ScrapedPage
    ) -> None:
        """ContentExtractionError is also raised when the readability text is too short."""
        very_short = "only five words here"  # 4 words — well below 50

        mock_doc = MagicMock()
        mock_doc.title.return_value = ""
        mock_doc.summary.return_value = f"<p>{very_short}</p>"

        mock_soup = MagicMock()
        mock_soup.get_text.return_value = very_short

        with (
            patch("trafilatura.extract", return_value=None),
            patch("trafilatura.extract_metadata", return_value=None),
            patch(
                "searchmuse.adapters.extractors.trafilatura_extractor.Document",
                return_value=mock_doc,
            ),
            patch(
                "searchmuse.adapters.extractors.trafilatura_extractor.BeautifulSoup",
                return_value=mock_soup,
            ),pytest.raises(ContentExtractionError)
        ):
            adapter.extract(sample_page)

    def test_no_error_when_word_count_exactly_at_minimum(
        self, adapter: TrafilaturaExtractorAdapter, sample_page: ScrapedPage
    ) -> None:
        """Exactly min_word_count words must NOT raise ContentExtractionError."""
        exact_text = " ".join(["word"] * _MIN_WORD_COUNT)
        meta = _make_metadata()
        with (
            patch("trafilatura.extract", return_value=exact_text),
            patch("trafilatura.extract_metadata", return_value=meta),
        ):
            result = adapter.extract(sample_page)  # must not raise

        assert result.word_count == _MIN_WORD_COUNT


# ---------------------------------------------------------------------------
# supports_content_type tests
# ---------------------------------------------------------------------------


class TestSupportsContentType:
    """Tests for the content-type guard method."""

    def test_supports_html(self, adapter: TrafilaturaExtractorAdapter) -> None:
        """HTML content type must be supported."""
        assert adapter.supports_content_type(ContentType.HTML) is True

    def test_supports_plain_text(self, adapter: TrafilaturaExtractorAdapter) -> None:
        """PLAIN_TEXT content type must be supported."""
        assert adapter.supports_content_type(ContentType.PLAIN_TEXT) is True

    def test_does_not_support_pdf(self, adapter: TrafilaturaExtractorAdapter) -> None:
        """PDF content type must not be supported."""
        assert adapter.supports_content_type(ContentType.PDF) is False

    def test_does_not_support_json(self, adapter: TrafilaturaExtractorAdapter) -> None:
        """JSON content type must not be supported."""
        assert adapter.supports_content_type(ContentType.JSON) is False
