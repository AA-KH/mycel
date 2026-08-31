"""
Memory Indexer (Phase 12 Memory System)

Responsibilities:
- In-memory tag and keyword index for fast scope-bounded relevance scoring.
- Calculates relevance scores based on tag match, title match, content match, and importance weights.
"""

import re
import logging
from typing import List, Dict, Set, Tuple, Optional
from memory.models import MemoryItem, MemoryScope, MemoryImportance

logger = logging.getLogger(__name__)

IMPORTANCE_WEIGHTS = {
    MemoryImportance.LOW: 1.0,
    MemoryImportance.MEDIUM: 1.2,
    MemoryImportance.HIGH: 1.5,
    MemoryImportance.CRITICAL: 2.0,
}


class MemoryIndexer:
    """
    In-memory tag & keyword index for MemoryItems.
    """

    def __init__(self):
        self._tag_index: Dict[str, Set[str]] = {}        # tag -> set of memory_ids
        self._token_index: Dict[str, Set[str]] = {}      # token -> set of memory_ids

    def index_item(self, item: MemoryItem) -> None:
        """
        Indexes a MemoryItem by tags and content tokens.
        """
        mid = item.memory_id

        # Index tags
        for tag in item.tags:
            tag_clean = tag.lower().strip()
            self._tag_index.setdefault(tag_clean, set()).add(mid)

        # Index tokens from title & content
        tokens = self._tokenize(f"{item.title} {item.content}")
        for token in tokens:
            self._token_index.setdefault(token, set()).add(mid)

    def remove_item(self, memory_id: str) -> None:
        """
        Removes a MemoryItem from tag and token indexes.
        """
        for s in self._tag_index.values():
            s.discard(memory_id)
        for s in self._token_index.values():
            s.discard(memory_id)

    def score_item(
        self,
        item: MemoryItem,
        keywords: List[str],
        tags: List[str],
    ) -> float:
        """
        Computes deterministic relevance score for item given query keywords & tags.
        """
        score = 0.0
        imp_weight = IMPORTANCE_WEIGHTS.get(item.importance, 1.0)

        # Tag match scoring (+2.0 per tag match)
        item_tags_set = {t.lower() for t in item.tags}
        for query_tag in tags:
            if query_tag.lower() in item_tags_set:
                score += 2.0

        # Title / Content keyword scoring (+1.0 title match, +0.5 content match)
        title_lower = item.title.lower()
        content_lower = item.content.lower()

        for kw in keywords:
            kw_clean = kw.lower().strip()
            if not kw_clean:
                continue
            if kw_clean in title_lower:
                score += 1.5
            elif kw_clean in content_lower:
                score += 0.5

        # Base score bonus if active & recent
        score += 0.1

        return score * imp_weight

    def _tokenize(self, text: str) -> Set[str]:
        words = re.findall(r'\b[a-zA-Z0-9_]{3,}\b', text.lower())
        return set(words)
