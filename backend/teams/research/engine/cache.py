"""
Research Engine — Cache Layer

In-memory LRU caching for search results and fetched content.
Tracks freshness metadata for research reuse decisions.
"""

import logging
import time
from collections import OrderedDict
from datetime import datetime, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ResearchCache:
    """
    Simple LRU cache for research data with freshness tracking.
    
    Separate caches for:
    - Search results (short TTL — queries may get stale)
    - Fetched pages (medium TTL — page content doesn't change every minute)
    - Research artifacts (long TTL — completed research is reusable)
    """
    
    def __init__(self, max_search_entries: int = 200, max_page_entries: int = 500,
                 search_ttl_seconds: int = 3600, page_ttl_seconds: int = 7200):
        self._search_cache: OrderedDict = OrderedDict()
        self._page_cache: OrderedDict = OrderedDict()
        
        self._max_search = max_search_entries
        self._max_pages = max_page_entries
        self._search_ttl = search_ttl_seconds
        self._page_ttl = page_ttl_seconds
        
        self._hits = 0
        self._misses = 0
    
    # --- Search Cache ---
    
    def get_search(self, query: str) -> Optional[Any]:
        """Get cached search results for a query."""
        key = query.strip().lower()
        entry = self._search_cache.get(key)
        if entry is None:
            self._misses += 1
            return None
        
        timestamp, data = entry
        if time.time() - timestamp > self._search_ttl:
            del self._search_cache[key]
            self._misses += 1
            return None
        
        # Move to end (most recently used)
        self._search_cache.move_to_end(key)
        self._hits += 1
        return data
    
    def set_search(self, query: str, data: Any):
        """Cache search results."""
        key = query.strip().lower()
        self._search_cache[key] = (time.time(), data)
        self._search_cache.move_to_end(key)
        
        # Evict oldest if over capacity
        while len(self._search_cache) > self._max_search:
            self._search_cache.popitem(last=False)
    
    # --- Page Cache ---
    
    def get_page(self, url: str) -> Optional[Any]:
        """Get cached page content for a URL."""
        entry = self._page_cache.get(url)
        if entry is None:
            self._misses += 1
            return None
        
        timestamp, data = entry
        if time.time() - timestamp > self._page_ttl:
            del self._page_cache[url]
            self._misses += 1
            return None
        
        self._page_cache.move_to_end(url)
        self._hits += 1
        return data
    
    def set_page(self, url: str, data: Any):
        """Cache page content."""
        self._page_cache[url] = (time.time(), data)
        self._page_cache.move_to_end(url)
        
        while len(self._page_cache) > self._max_pages:
            self._page_cache.popitem(last=False)
    
    # --- Stats ---
    
    @property
    def hit_rate(self) -> float:
        total = self._hits + self._misses
        return self._hits / total if total > 0 else 0.0
    
    @property
    def stats(self) -> Dict[str, Any]:
        return {
            "search_entries": len(self._search_cache),
            "page_entries": len(self._page_cache),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(self.hit_rate, 3)
        }
    
    def clear(self):
        """Clear all caches."""
        self._search_cache.clear()
        self._page_cache.clear()
        self._hits = 0
        self._misses = 0


# Singleton cache instance
research_cache = ResearchCache()
