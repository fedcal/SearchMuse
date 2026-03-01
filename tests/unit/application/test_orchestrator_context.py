"""Unit tests for chat context passing through the orchestrator.

Verifies that chat_context is properly forwarded from the orchestrator
to the LLM adapter's generate_search_strategy method.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import pytest

from searchmuse.application.search_orchestrator import SearchOrchestrator
from searchmuse.domain.enums import RelevanceScore
from searchmuse.domain.models import SearchStrategy

if TYPE_CHECKING:
    from searchmuse.infrastructure.config import SearchMuseConfig


def _make_strategy(query_id: str = "q1", iteration: int = 1) -> SearchStrategy:
    return SearchStrategy(
        strategy_id="strat-001",
        query_id=query_id,
        search_terms=("test query",),
        target_domains=(),
        reasoning="Testing",
        iteration=iteration,
    )


@pytest.fixture()
def mock_llm() -> AsyncMock:
    llm = AsyncMock()
    llm.generate_search_strategy = AsyncMock(return_value=_make_strategy())
    llm.assess_content_relevance = AsyncMock(return_value=RelevanceScore.HIGH)
    llm.assess_coverage = AsyncMock(return_value=(0.9, "Good coverage"))
    llm.synthesize_answer = AsyncMock(return_value="Synthesized answer.")
    return llm


@pytest.fixture()
def mock_search() -> AsyncMock:
    search = AsyncMock()
    search.search = AsyncMock(return_value=())
    return search


@pytest.fixture()
def mock_scraper() -> AsyncMock:
    scraper = AsyncMock()
    scraper.scrape_many = AsyncMock(return_value=())
    return scraper


@pytest.fixture()
def mock_extractor() -> MagicMock:
    return MagicMock()


@pytest.fixture()
def mock_repository() -> AsyncMock:
    return AsyncMock()


@pytest.fixture()
def orchestrator(
    test_config: SearchMuseConfig,
    mock_llm: AsyncMock,
    mock_search: AsyncMock,
    mock_scraper: AsyncMock,
    mock_extractor: MagicMock,
    mock_repository: AsyncMock,
) -> SearchOrchestrator:
    return SearchOrchestrator(
        config=test_config,
        llm=mock_llm,
        search=mock_search,
        scraper=mock_scraper,
        extractor=mock_extractor,
        repository=mock_repository,
    )


class TestOrchestratorContextPassing:
    """run() must forward chat_context to the LLM strategy method."""

    async def test_context_passed_to_llm(
        self,
        orchestrator: SearchOrchestrator,
        mock_llm: AsyncMock,
    ) -> None:
        context = (("previous query", "previous answer"),)
        await orchestrator.run("new query", chat_context=context)

        call_args = mock_llm.generate_search_strategy.call_args
        assert call_args is not None
        # chat_context should be the 3rd positional arg or a keyword arg
        args, kwargs = call_args
        if len(args) >= 3:
            assert args[2] == context
        else:
            assert kwargs.get("chat_context") == context

    async def test_empty_context_by_default(
        self,
        orchestrator: SearchOrchestrator,
        mock_llm: AsyncMock,
    ) -> None:
        await orchestrator.run("simple query")

        call_args = mock_llm.generate_search_strategy.call_args
        assert call_args is not None
        args, kwargs = call_args
        if len(args) >= 3:
            assert args[2] == ()
        else:
            assert kwargs.get("chat_context", ()) == ()

    async def test_result_returned_with_context(
        self,
        orchestrator: SearchOrchestrator,
    ) -> None:
        context = (("q1", "a1"), ("q2", "a2"))
        result = await orchestrator.run("query with context", chat_context=context)
        assert result.synthesis == "Synthesized answer."

    async def test_multi_entry_context(
        self,
        orchestrator: SearchOrchestrator,
        mock_llm: AsyncMock,
    ) -> None:
        context = tuple((f"q{i}", f"a{i}") for i in range(5))
        await orchestrator.run("query", chat_context=context)

        call_args = mock_llm.generate_search_strategy.call_args
        assert call_args is not None
        args, kwargs = call_args
        passed_context = args[2] if len(args) >= 3 else kwargs.get("chat_context", ())
        assert len(passed_context) == 5
