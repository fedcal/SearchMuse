"""DuckDuckGo search adapter implementing the SearchPort protocol.

Wraps the synchronous ``duckduckgo_search.DDGS.text()`` API inside
``asyncio.to_thread`` so callers can ``await`` it without blocking the event
loop.  All DDGS failures are translated into :class:`ScrapingError` to keep
the domain insulated from third-party exceptions.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from duckduckgo_search import DDGS

from searchmuse.domain.errors import ScrapingError
from searchmuse.domain.models import SearchHit

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Internal constants
# ---------------------------------------------------------------------------

_DEFAULT_MAX_RESULTS: int = 10
_DEFAULT_REGION: str = "wt-wt"  # worldwide, language-neutral
_DEFAULT_SAFESEARCH: str = "moderate"
_DEFAULT_TIMELIMIT: str | None = None  # no restriction


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _build_search_hit(raw: dict[str, Any]) -> SearchHit:
    """Convert a single DDGS result dict into an immutable :class:`SearchHit`.

    Args:
        raw: A dict produced by ``DDGS.text()`` with at minimum the keys
            ``"href"``, ``"title"``, and ``"body"``.

    Returns:
        A new, frozen :class:`SearchHit` instance.
    """
    return SearchHit(
        url=str(raw.get("href", "")),
        title=str(raw.get("title", "")),
        snippet=str(raw.get("body", "")),
    )


def _run_ddgs_text(
    query: str,
    *,
    max_results: int,
    region: str,
    safesearch: str,
    timelimit: str | None,
) -> list[dict[str, Any]]:
    """Execute ``DDGS.text()`` synchronously and return raw result dicts.

    Instantiating :class:`DDGS` per call is intentional — the library is
    documented as stateless across requests and carries no persistent session.

    Args:
        query: The search string to send to DuckDuckGo.
        max_results: Maximum number of results to request.
        region: DuckDuckGo region code (e.g. ``"wt-wt"`` for worldwide).
        safesearch: SafeSearch level: ``"on"``, ``"moderate"``, or ``"off"``.
        timelimit: Optional time constraint (``"d"``, ``"w"``, ``"m"``, ``"y"``).

    Returns:
        A list of raw result dicts from DDGS.  May be empty if no results
        were found for the query.
    """
    with DDGS() as ddgs:
        results: list[dict[str, Any]] = list(
            ddgs.text(
                query,
                region=region,
                safesearch=safesearch,
                timelimit=timelimit,
                max_results=max_results,
            )
        )
    return results


# ---------------------------------------------------------------------------
# Adapter
# ---------------------------------------------------------------------------


class DuckDuckGoSearchAdapter:
    """Async search adapter backed by DuckDuckGo via ``duckduckgo-search``.

    This adapter satisfies the ``SearchPort`` protocol.  Because
    ``DDGS.text()`` is synchronous and may perform blocking network I/O, every
    call is dispatched to a thread via :func:`asyncio.to_thread` so the event
    loop remains unblocked.

    All configuration is optional; sensible defaults are applied when omitted.

    Args:
        max_results: Default result cap used when the caller does not supply
            one.  Overridden on a per-call basis by the ``max_results``
            argument of :meth:`search`.
        region: DuckDuckGo region token (default ``"wt-wt"`` — worldwide).
        safesearch: SafeSearch setting: ``"on"``, ``"moderate"``, or ``"off"``.
        timelimit: Optional freshness filter.  Pass ``"d"``, ``"w"``, ``"m"``,
            or ``"y"`` to restrict results to the last day/week/month/year.

    Example::

        adapter = DuckDuckGoSearchAdapter(max_results=5)
        hits = await adapter.search("python asyncio patterns")
        await adapter.close()
    """

    def __init__(
        self,
        *,
        max_results: int = _DEFAULT_MAX_RESULTS,
        region: str = _DEFAULT_REGION,
        safesearch: str = _DEFAULT_SAFESEARCH,
        timelimit: str | None = _DEFAULT_TIMELIMIT,
    ) -> None:
        self._default_max_results: int = max_results
        self._region: str = region
        self._safesearch: str = safesearch
        self._timelimit: str | None = timelimit

    async def search(self, query: str, *, max_results: int = 10) -> tuple[SearchHit, ...]:
        """Perform an async web search using DuckDuckGo.

        The underlying ``DDGS.text()`` call is executed in a thread pool to
        avoid blocking the asyncio event loop.

        Args:
            query: The search string.  Must be a non-empty string.
            max_results: Upper bound on the number of results to return.
                The protocol default is 10; the instance default configured at
                construction time takes precedence only when the caller relies
                on the protocol default.

        Returns:
            An immutable tuple of :class:`SearchHit` objects ordered as
            returned by DuckDuckGo.  May be empty when the query yields no
            results.

        Raises:
            ScrapingError: Wraps any exception raised by ``DDGS.text()`` so
                that callers are not coupled to the third-party library's
                exception hierarchy.
        """
        effective_max = max_results

        logger.debug("DuckDuckGo search: query=%r max_results=%d", query, effective_max)

        try:
            raw_results: list[dict[str, Any]] = await asyncio.to_thread(
                _run_ddgs_text,
                query,
                max_results=effective_max,
                region=self._region,
                safesearch=self._safesearch,
                timelimit=self._timelimit,
            )
        except Exception as exc:
            logger.error("DuckDuckGo search failed for query=%r: %s", query, exc)
            raise ScrapingError(
                f"DuckDuckGo search failed: {exc}",
                url=query,
            ) from exc

        hits: tuple[SearchHit, ...] = tuple(_build_search_hit(r) for r in raw_results)

        logger.debug("DuckDuckGo returned %d hits for query=%r", len(hits), query)
        return hits

    async def close(self) -> None:
        """No-op teardown method required by the ``SearchPort`` protocol.

        ``DDGS`` is instantiated and destroyed within each :meth:`search`
        call, so there is no persistent connection or session to release.
        """
