"""Unit tests for SqliteRepositoryAdapter.

Uses a temporary on-disk SQLite database (via tmp_path) so each test gets a
clean slate without requiring any external services.  All async tests run
automatically via asyncio_mode = "auto" (pytest-asyncio).
"""

from __future__ import annotations

import dataclasses
from datetime import UTC, datetime
from pathlib import Path  # noqa: TC003 - used at runtime by pytest tmp_path fixtures

import pytest

from searchmuse.adapters.repositories.sqlite_repository import SqliteRepositoryAdapter
from searchmuse.domain.enums import RelevanceScore
from searchmuse.domain.models import Source

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_NOW = datetime(2024, 6, 1, 12, 0, 0, tzinfo=UTC)
_LATER = datetime(2024, 6, 2, 8, 0, 0, tzinfo=UTC)


def _make_source(
    *,
    source_id: str = "src-001",
    content_id: str = "cid-001",
    url: str = "https://example.com/article",
    title: str = "Example Article",
    snippet: str = "A short excerpt.",
    relevance_score: RelevanceScore = RelevanceScore.HIGH,
    credibility_notes: str = "Reputable journal.",
    author: str | None = None,
    accessed_at: datetime = _NOW,
) -> Source:
    """Create a Source with sensible defaults, overridable per test."""
    return Source(
        source_id=source_id,
        content_id=content_id,
        url=url,
        title=title,
        snippet=snippet,
        relevance_score=relevance_score,
        credibility_notes=credibility_notes,
        author=author,
        accessed_at=accessed_at,
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
async def repo(tmp_path: Path) -> SqliteRepositoryAdapter:
    """Return a fresh SqliteRepositoryAdapter backed by a temp file.

    The adapter is closed after each test to release the file handle.
    """
    db_file = tmp_path / "test_searchmuse.db"
    adapter = SqliteRepositoryAdapter(db_path=str(db_file))
    yield adapter  # type: ignore[misc]
    await adapter.close()


# ---------------------------------------------------------------------------
# save + find_by_id round-trip
# ---------------------------------------------------------------------------


class TestSaveAndFindById:
    """save followed by find_by_id must return an equivalent Source."""

    async def test_round_trip_returns_source(
        self, repo: SqliteRepositoryAdapter
    ) -> None:
        source = _make_source()
        await repo.save(source, session_id="sess-001")

        result = await repo.find_by_id(source.source_id)

        assert result is not None

    async def test_round_trip_source_id_matches(
        self, repo: SqliteRepositoryAdapter
    ) -> None:
        source = _make_source(source_id="sid-abc")
        await repo.save(source, session_id="sess-001")

        result = await repo.find_by_id("sid-abc")

        assert result is not None
        assert result.source_id == "sid-abc"

    async def test_round_trip_url_matches(self, repo: SqliteRepositoryAdapter) -> None:
        source = _make_source(url="https://example.com/specific-article")
        await repo.save(source, session_id="sess-001")

        result = await repo.find_by_id(source.source_id)

        assert result is not None
        assert result.url == "https://example.com/specific-article"

    async def test_round_trip_title_matches(self, repo: SqliteRepositoryAdapter) -> None:
        source = _make_source(title="My Important Title")
        await repo.save(source, session_id="sess-001")

        result = await repo.find_by_id(source.source_id)

        assert result is not None
        assert result.title == "My Important Title"

    async def test_round_trip_snippet_matches(self, repo: SqliteRepositoryAdapter) -> None:
        source = _make_source(snippet="A telling excerpt from the article.")
        await repo.save(source, session_id="sess-001")

        result = await repo.find_by_id(source.source_id)

        assert result is not None
        assert result.snippet == "A telling excerpt from the article."

    async def test_round_trip_relevance_score_matches(
        self, repo: SqliteRepositoryAdapter
    ) -> None:
        source = _make_source(relevance_score=RelevanceScore.MEDIUM)
        await repo.save(source, session_id="sess-001")

        result = await repo.find_by_id(source.source_id)

        assert result is not None
        assert result.relevance_score == RelevanceScore.MEDIUM

    async def test_round_trip_author_none_preserved(
        self, repo: SqliteRepositoryAdapter
    ) -> None:
        source = _make_source(author=None)
        await repo.save(source, session_id="sess-001")

        result = await repo.find_by_id(source.source_id)

        assert result is not None
        assert result.author is None

    async def test_round_trip_author_string_preserved(
        self, repo: SqliteRepositoryAdapter
    ) -> None:
        source = _make_source(author="Jane Doe")
        await repo.save(source, session_id="sess-001")

        result = await repo.find_by_id(source.source_id)

        assert result is not None
        assert result.author == "Jane Doe"

    async def test_round_trip_accessed_at_preserved(
        self, repo: SqliteRepositoryAdapter
    ) -> None:
        source = _make_source(accessed_at=_NOW)
        await repo.save(source, session_id="sess-001")

        result = await repo.find_by_id(source.source_id)

        assert result is not None
        # Compare without sub-second precision that ISO format may drop.
        assert result.accessed_at.replace(microsecond=0) == _NOW.replace(microsecond=0)

    async def test_returned_source_is_frozen(self, repo: SqliteRepositoryAdapter) -> None:
        source = _make_source()
        await repo.save(source, session_id="sess-001")

        result = await repo.find_by_id(source.source_id)

        assert result is not None
        with pytest.raises(dataclasses.FrozenInstanceError):
            result.title = "mutated"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# find_by_id — missing record
# ---------------------------------------------------------------------------


class TestFindByIdMissing:
    """find_by_id must return None for unknown IDs."""

    async def test_returns_none_for_missing_id(self, repo: SqliteRepositoryAdapter) -> None:
        result = await repo.find_by_id("nonexistent-id")

        assert result is None

    async def test_returns_none_on_empty_database(self, repo: SqliteRepositoryAdapter) -> None:
        result = await repo.find_by_id("any-id")

        assert result is None


# ---------------------------------------------------------------------------
# find_by_session
# ---------------------------------------------------------------------------


class TestFindBySession:
    """find_by_session must return all sources saved under that session ID."""

    async def test_returns_sources_for_matching_session(
        self, repo: SqliteRepositoryAdapter
    ) -> None:
        src_a = _make_source(source_id="a", url="https://a.com/")
        src_b = _make_source(source_id="b", url="https://b.com/")
        await repo.save(src_a, session_id="session-X")
        await repo.save(src_b, session_id="session-X")

        results = await repo.find_by_session("session-X")

        assert len(results) == 2

    async def test_does_not_return_other_session_sources(
        self, repo: SqliteRepositoryAdapter
    ) -> None:
        src_a = _make_source(source_id="a", url="https://a.com/")
        src_b = _make_source(source_id="b", url="https://b.com/")
        await repo.save(src_a, session_id="session-X")
        await repo.save(src_b, session_id="session-Y")

        results = await repo.find_by_session("session-X")

        assert len(results) == 1
        assert results[0].source_id == "a"

    async def test_returns_empty_tuple_for_unknown_session(
        self, repo: SqliteRepositoryAdapter
    ) -> None:
        results = await repo.find_by_session("no-such-session")

        assert results == ()

    async def test_returns_tuple_type(self, repo: SqliteRepositoryAdapter) -> None:
        src = _make_source()
        await repo.save(src, session_id="sess")

        results = await repo.find_by_session("sess")

        assert isinstance(results, tuple)

    async def test_sources_contain_correct_ids(
        self, repo: SqliteRepositoryAdapter
    ) -> None:
        src_a = _make_source(source_id="a", url="https://a.com/")
        src_b = _make_source(source_id="b", url="https://b.com/")
        await repo.save(src_a, session_id="my-session")
        await repo.save(src_b, session_id="my-session")

        results = await repo.find_by_session("my-session")
        result_ids = {r.source_id for r in results}

        assert result_ids == {"a", "b"}


# ---------------------------------------------------------------------------
# find_by_url
# ---------------------------------------------------------------------------


class TestFindByUrl:
    """find_by_url must return the most recently saved source for that URL."""

    async def test_returns_source_for_known_url(self, repo: SqliteRepositoryAdapter) -> None:
        src = _make_source(url="https://target.com/page")
        await repo.save(src, session_id="sess")

        result = await repo.find_by_url("https://target.com/page")

        assert result is not None
        assert result.url == "https://target.com/page"

    async def test_returns_none_for_unknown_url(self, repo: SqliteRepositoryAdapter) -> None:
        result = await repo.find_by_url("https://unknown.com/")

        assert result is None

    async def test_returns_most_recent_when_url_saved_twice(
        self, repo: SqliteRepositoryAdapter
    ) -> None:
        url = "https://example.com/article"
        older = _make_source(
            source_id="old",
            url=url,
            title="Old Version",
            accessed_at=_NOW,
        )
        newer = _make_source(
            source_id="new",
            url=url,
            title="New Version",
            accessed_at=_LATER,
        )
        await repo.save(older, session_id="sess")
        await repo.save(newer, session_id="sess")

        result = await repo.find_by_url(url)

        assert result is not None
        assert result.source_id == "new"
        assert result.title == "New Version"


# ---------------------------------------------------------------------------
# save — upsert behaviour
# ---------------------------------------------------------------------------


class TestSaveUpsert:
    """save must replace an existing row when the source_id already exists."""

    async def test_upsert_replaces_existing_record(
        self, repo: SqliteRepositoryAdapter
    ) -> None:
        original = _make_source(source_id="upsert-id", title="Original Title")
        replacement = _make_source(source_id="upsert-id", title="Replaced Title")

        await repo.save(original, session_id="sess")
        await repo.save(replacement, session_id="sess")

        result = await repo.find_by_id("upsert-id")
        assert result is not None
        assert result.title == "Replaced Title"

    async def test_upsert_keeps_only_one_row_per_source_id(
        self, repo: SqliteRepositoryAdapter
    ) -> None:
        src = _make_source(source_id="dup-id", url="https://a.com/")
        updated = _make_source(source_id="dup-id", url="https://b.com/")

        await repo.save(src, session_id="sess")
        await repo.save(updated, session_id="sess")

        results = await repo.find_by_session("sess")
        matching = [r for r in results if r.source_id == "dup-id"]
        assert len(matching) == 1

    async def test_save_multiple_distinct_sources(
        self, repo: SqliteRepositoryAdapter
    ) -> None:
        sources = [
            _make_source(source_id=f"id-{i}", url=f"https://site{i}.com/")
            for i in range(5)
        ]
        for src in sources:
            await repo.save(src, session_id="bulk-sess")

        results = await repo.find_by_session("bulk-sess")
        assert len(results) == 5


# ---------------------------------------------------------------------------
# close — lifecycle
# ---------------------------------------------------------------------------


class TestClose:
    """close must be idempotent and safe to call multiple times."""

    async def test_close_before_any_operation_is_noop(self, tmp_path: Path) -> None:
        db_file = tmp_path / "close_test.db"
        adapter = SqliteRepositoryAdapter(db_path=str(db_file))

        await adapter.close()  # must not raise

    async def test_double_close_is_safe(self, tmp_path: Path) -> None:
        db_file = tmp_path / "double_close.db"
        adapter = SqliteRepositoryAdapter(db_path=str(db_file))
        src = _make_source()
        await adapter.save(src, session_id="sess")

        await adapter.close()
        await adapter.close()  # second call must also not raise

    async def test_connection_is_none_after_close(self, tmp_path: Path) -> None:
        db_file = tmp_path / "conn_none.db"
        adapter = SqliteRepositoryAdapter(db_path=str(db_file))
        src = _make_source()
        await adapter.save(src, session_id="sess")
        await adapter.close()

        assert adapter._connection is None
