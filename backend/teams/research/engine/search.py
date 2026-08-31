"""
Research Engine — Search Provider Abstraction

Provides a clean interface for web search with DuckDuckGo as the default provider.
Supports query generation, result deduplication, and search iteration.
"""

import asyncio
import logging
import hashlib
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Set
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class SearchResult(object):
    """A single search result."""
    __slots__ = ('title', 'url', 'snippet', 'domain', 'searched_at')
    
    def __init__(self, title: str, url: str, snippet: str):
        self.title = title
        self.url = url
        self.snippet = snippet
        self.domain = urlparse(url).netloc if url else ""
        self.searched_at = datetime.now(timezone.utc)
    
    def __repr__(self):
        return f"SearchResult(title='{self.title[:40]}...', url='{self.url}')"
    
    def __eq__(self, other):
        return isinstance(other, SearchResult) and self.url == other.url
    
    def __hash__(self):
        return hash(self.url)


class SearchProvider(ABC):
    """Abstract search provider interface."""
    
    @abstractmethod
    async def search(self, query: str, max_results: int = 8) -> List[SearchResult]:
        """Execute a search query and return results."""
        pass


class DuckDuckGoSearchProvider(SearchProvider):
    """Free web search using DuckDuckGo. No API key required."""
    
    def __init__(self, region: str = "wt-wt"):
        self.region = region
        self._semaphore = asyncio.Semaphore(3)  # Rate limit
    
    async def search(self, query: str, max_results: int = 8) -> List[SearchResult]:
        """Execute a DuckDuckGo search."""
        async with self._semaphore:
            try:
                results = await asyncio.get_event_loop().run_in_executor(
                    None, self._do_search, query, min(max_results, 20)
                )
                logger.info(f"[DDG] '{query}' → {len(results)} results")
                return results
            except Exception as e:
                logger.error(f"[DDG] Search failed for '{query}': {e}")
                return []
    
    def _do_search(self, query: str, max_results: int) -> List[SearchResult]:
        from duckduckgo_search import DDGS
        results = []
        try:
            with DDGS() as ddgs:
                for r in ddgs.text(query, region=self.region, max_results=max_results):
                    results.append(SearchResult(
                        title=r.get("title", ""),
                        url=r.get("href", r.get("link", "")),
                        snippet=r.get("body", r.get("snippet", ""))
                    ))
        except Exception as e:
            logger.error(f"[DDG] Internal search error: {e}")
        return results


class SearchEngine:
    """
    High-level search engine that wraps a SearchProvider with:
    - Query deduplication
    - Result deduplication (by URL)
    - Source tracking
    - Search iteration support
    """
    
    def __init__(self, provider: Optional[SearchProvider] = None):
        self.provider = provider or DuckDuckGoSearchProvider()
        self._executed_queries: Set[str] = set()
        self._all_results: Dict[str, SearchResult] = {}  # url → result
        self._search_count = 0
    
    async def search(self, query: str, max_results: int = 8) -> List[SearchResult]:
        """Execute a search, deduplicating queries and results."""
        query_key = query.strip().lower()
        if query_key in self._executed_queries:
            logger.debug(f"[SearchEngine] Skipping duplicate query: '{query}'")
            # Return cached results that match
            return [r for r in self._all_results.values() 
                    if query_key in (r.title.lower() + r.snippet.lower())]
        
        self._executed_queries.add(query_key)
        self._search_count += 1
        
        results = await self.provider.search(query, max_results)
        
        # Deduplicate by URL
        new_results = []
        for r in results:
            if r.url and r.url not in self._all_results:
                self._all_results[r.url] = r
                new_results.append(r)
        
        return results  # Return all results, dedup tracking is internal
    
    async def multi_search(self, queries: List[str], max_results_per_query: int = 5) -> List[SearchResult]:
        """Execute multiple queries in parallel and merge results."""
        tasks = [self.search(q, max_results_per_query) for q in queries]
        results_lists = await asyncio.gather(*tasks, return_exceptions=True)
        
        merged = []
        seen_urls = set()
        for result_or_error in results_lists:
            if isinstance(result_or_error, Exception):
                logger.error(f"[SearchEngine] Multi-search error: {result_or_error}")
                continue
            for r in result_or_error:
                if r.url not in seen_urls:
                    seen_urls.add(r.url)
                    merged.append(r)
        
        return merged
    
    @property
    def total_searches(self) -> int:
        return self._search_count
    
    @property
    def total_unique_results(self) -> int:
        return len(self._all_results)
    
    def get_all_discovered_urls(self) -> List[str]:
        return list(self._all_results.keys())


# ─────────────────────────────────────────────────────────────
# Query Generation
# ─────────────────────────────────────────────────────────────

def generate_entity_queries(entity: str) -> List[str]:
    """Generate a diverse set of search queries for an entity (company/product)."""
    return [
        f"{entity}",
        f"{entity} products features",
        f"{entity} pricing plans",
        f"{entity} reviews",
        f"{entity} competitors alternatives",
        f"{entity} pros cons",
        f'"{entity}" site:reddit.com',
        f"{entity} documentation API",
        f"{entity} latest news 2026",
        f"{entity} customer complaints problems",
    ]


def generate_comparison_queries(entities: List[str]) -> List[str]:
    """Generate comparison queries between entities."""
    queries = []
    for i, e1 in enumerate(entities):
        for e2 in entities[i+1:]:
            queries.append(f"{e1} vs {e2}")
            queries.append(f"{e1} vs {e2} comparison")
    for entity in entities:
        queries.append(f"{entity} pricing plans cost")
        queries.append(f"{entity} reviews")
    return queries


def generate_technical_queries(topic: str) -> List[str]:
    """Generate queries for technical research."""
    return [
        f"{topic}",
        f"{topic} tutorial guide",
        f"{topic} documentation",
        f"{topic} github",
        f"{topic} best practices",
        f"{topic} performance benchmark",
        f"{topic} alternatives",
        f"{topic} limitations drawbacks",
    ]
