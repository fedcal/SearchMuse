"""Domain validators for raw input at system boundaries."""

from searchmuse.domain.errors import ValidationError

_QUERY_MIN_LENGTH: int = 1
_QUERY_MAX_LENGTH: int = 5000
_ALLOWED_URL_SCHEMES: tuple[str, ...] = ("http://", "https://")


def validate_query(raw_text: str) -> str:
    """Validate and normalise a raw search query string.

    Args:
        raw_text: The raw query text provided by the caller.

    Returns:
        Stripped, validated query text ready for downstream use.

    Raises:
        ValidationError: If the query is empty or exceeds length limits.
    """
    stripped = raw_text.strip()

    if len(stripped) < _QUERY_MIN_LENGTH:
        raise ValidationError(
            "Query must not be empty",
            field="query",
            detail="Received an empty or whitespace-only string",
        )

    if len(stripped) > _QUERY_MAX_LENGTH:
        raise ValidationError(
            "Query exceeds maximum length",
            field="query",
            detail=f"Limit is {_QUERY_MAX_LENGTH} characters, got {len(stripped)}",
        )

    return stripped


def validate_url(url: str) -> str:
    """Validate that a URL uses an allowed scheme.

    Args:
        url: The URL string to validate.

    Returns:
        The original URL unchanged if valid.

    Raises:
        ValidationError: If the URL does not start with http:// or https://.
    """
    stripped = url.strip()

    if not any(stripped.startswith(scheme) for scheme in _ALLOWED_URL_SCHEMES):
        raise ValidationError(
            "URL must use http or https scheme",
            field="url",
            detail=f"Received: {stripped!r}",
        )

    return stripped


def validate_iteration_count(count: int, max_count: int) -> None:
    """Ensure the iteration count has not exceeded the configured maximum.

    Args:
        count: Current number of iterations performed.
        max_count: Maximum allowed iterations from configuration.

    Raises:
        ValidationError: If count is greater than or equal to max_count.
    """
    if count >= max_count:
        raise ValidationError(
            "Maximum iteration count reached",
            field="iteration_count",
            detail=f"Performed {count} iterations; limit is {max_count}",
        )
