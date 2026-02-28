"""Scraper adapter implementations (httpx, DuckDuckGo, etc.)."""

from searchmuse.adapters.scrapers.duckduckgo_search import DuckDuckGoSearchAdapter
from searchmuse.adapters.scrapers.httpx_scraper import HttpxScraperAdapter

__all__ = ["DuckDuckGoSearchAdapter", "HttpxScraperAdapter"]
