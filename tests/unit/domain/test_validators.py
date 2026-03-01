"""Tests for searchmuse.domain.validators."""

import pytest

from searchmuse.domain.errors import ValidationError
from searchmuse.domain.validators import (
    validate_iteration_count,
    validate_query,
    validate_url,
)


def test_validate_query_strips_whitespace():
    result = validate_query("  hello  ")
    assert result == "hello"


def test_validate_query_empty_raises():
    with pytest.raises(ValidationError):
        validate_query("")


def test_validate_query_whitespace_only_raises():
    with pytest.raises(ValidationError):
        validate_query("   ")


def test_validate_query_too_long():
    with pytest.raises(ValidationError, match="5000"):
        validate_query("a" * 5001)


def test_validate_query_max_length_ok():
    result = validate_query("a" * 5000)
    assert len(result) == 5000


def test_validate_url_http():
    assert validate_url("http://example.com") == "http://example.com"


def test_validate_url_https():
    assert validate_url("https://example.com/path") == "https://example.com/path"


def test_validate_url_strips():
    assert validate_url("  https://example.com  ") == "https://example.com"


def test_validate_url_ftp_raises():
    with pytest.raises(ValidationError):
        validate_url("ftp://example.com")


def test_validate_url_no_scheme_raises():
    with pytest.raises(ValidationError):
        validate_url("example.com")


def test_validate_iteration_count_within_limit():
    validate_iteration_count(2, 5)


def test_validate_iteration_count_at_limit():
    with pytest.raises(ValidationError):
        validate_iteration_count(5, 5)


def test_validate_iteration_count_over_limit():
    with pytest.raises(ValidationError):
        validate_iteration_count(10, 5)
