"""Dependency injection container for SearchMuse CLI.

Wires adapter implementations to port interfaces and builds
the SearchOrchestrator with all dependencies resolved.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from searchmuse.adapters.extractors.trafilatura_extractor import TrafilaturaExtractorAdapter
from searchmuse.adapters.llm import create_llm_adapter
from searchmuse.adapters.renderers.markdown_renderer import MarkdownRendererAdapter
from searchmuse.adapters.repositories.sqlite_repository import SqliteRepositoryAdapter
from searchmuse.adapters.scrapers.duckduckgo_search import DuckDuckGoSearchAdapter
from searchmuse.adapters.scrapers.httpx_scraper import HttpxScraperAdapter
from searchmuse.application.search_orchestrator import SearchOrchestrator
from searchmuse.infrastructure.config import SearchMuseConfig, load_config

if TYPE_CHECKING:
    from searchmuse.adapters.llm._base import BaseLLMAdapter
    from searchmuse.application.progress import ProgressCallback


class Container:
    """Holds all wired dependencies for a SearchMuse session.

    Constructed from a SearchMuseConfig; provides accessor properties
    for the orchestrator and individual adapters.
    """

    def __init__(
        self,
        config: SearchMuseConfig,
        *,
        progress: ProgressCallback | None = None,
    ) -> None:
        self._config = config
        self._progress = progress

        self._llm: BaseLLMAdapter = create_llm_adapter(config.llm)
        self._search = DuckDuckGoSearchAdapter()
        self._scraper = HttpxScraperAdapter(config=config.scraping)
        self._extractor = TrafilaturaExtractorAdapter(config=config.extraction)

        db_path = str(Path(config.storage.db_path).expanduser())
        self._repository = SqliteRepositoryAdapter(db_path=db_path)
        self._renderer = MarkdownRendererAdapter()

        self._orchestrator = SearchOrchestrator(
            config=config,
            llm=self._llm,
            search=self._search,
            scraper=self._scraper,
            extractor=self._extractor,
            repository=self._repository,
            progress=progress,
        )

    @property
    def config(self) -> SearchMuseConfig:
        return self._config

    @property
    def orchestrator(self) -> SearchOrchestrator:
        return self._orchestrator

    @property
    def renderer(self) -> MarkdownRendererAdapter:
        return self._renderer

    async def close(self) -> None:
        """Release all held resources."""
        await self._search.close()
        await self._scraper.close()
        await self._repository.close()


def build_container(
    *,
    config_path: Path | None = None,
    progress: ProgressCallback | None = None,
) -> Container:
    """Build a fully-wired Container from configuration.

    Args:
        config_path: Optional path to user YAML config override.
        progress: Optional progress callback for the orchestrator.

    Returns:
        A Container with all dependencies resolved.
    """
    config = load_config(config_path)
    return Container(config, progress=progress)
