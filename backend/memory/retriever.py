"""
Memory Retriever (Phase 12 Memory System)

Responsibilities:
- Queries and ranks MemoryItems by scope, tags, keywords, and importance thresholds.
- Supports scope hierarchy fallback (e.g., TEAM scope query falls back to ORGANIZATION scope).
- Returns MemoryQueryResult objects containing relevance scores and match reasons.
"""

import logging
from typing import List, Optional

from memory.models import (
    MemoryItem,
    MemoryScope,
    MemoryImportance,
    MemoryQueryResult,
)
from memory.store import MemoryStore
from memory.indexer import MemoryIndexer

logger = logging.getLogger(__name__)


class MemoryRetriever:
    """
    Deterministic retrieval engine for MemoryItems.
    """

    def __init__(self, store: MemoryStore, indexer: MemoryIndexer):
        self._store = store
        self._indexer = indexer

    def query_memories(
        self,
        scope: MemoryScope,
        scope_id: str,
        keywords: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        min_importance: Optional[MemoryImportance] = None,
        min_score: float = 0.1,
        limit: int = 5,
        include_organization_scope: bool = True,
    ) -> List[MemoryQueryResult]:
        """
        Queries and ranks active MemoryItems matching scope, keywords, and tags.
        """
        query_keywords = keywords or []
        query_tags = tags or []

        # 1. Fetch candidate items for primary scope
        candidates = self._store.list_active_by_scope(scope, scope_id)

        # 2. Add Organization scope candidates if requested (cross-scope sharing)
        if include_organization_scope and scope != MemoryScope.ORGANIZATION:
            org_candidates = self._store.list_active_by_scope(
                MemoryScope.ORGANIZATION, "mycel_global"
            )
            candidates.extend(org_candidates)

        results: List[MemoryQueryResult] = []

        for item in candidates:
            # Importance filter if specified
            if min_importance and not self._meets_min_importance(item.importance, min_importance):
                continue

            score = self._indexer.score_item(item, query_keywords, query_tags)

            if score >= min_score:
                reason = f"Matched scope '{item.scope.value}' (Score: {score:.2f})"
                results.append(
                    MemoryQueryResult(
                        memory_item=item,
                        score=score,
                        match_reason=reason,
                    )
                )

        # Sort descending by relevance score
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:limit]

    def _meets_min_importance(
        self, importance: MemoryImportance, min_importance: MemoryImportance
    ) -> bool:
        importance_order = [
            MemoryImportance.LOW,
            MemoryImportance.MEDIUM,
            MemoryImportance.HIGH,
            MemoryImportance.CRITICAL,
        ]
        return importance_order.index(importance) >= importance_order.index(min_importance)
