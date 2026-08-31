"""
Memory Context Projector (Phase 12 Memory System)

Responsibilities:
- Projects relevant MemoryItems into lightweight context representations for Agents & WorkUnits.
- Enforces Memory is NOT Context (Memory is persistent store; Context is pruned runtime view).
- Formats memory summaries cleanly without exposing raw transcripts or credentials.
"""

import logging
from typing import List, Dict, Any

from memory.models import MemoryItem, MemoryQueryResult

logger = logging.getLogger(__name__)


class MemoryContextProjector:
    """
    Projects MemoryQueryResult lists into clean context dictionaries for LLM/Agent consumption.
    """

    def project_memories_to_context(
        self, query_results: List[MemoryQueryResult]
    ) -> List[Dict[str, Any]]:
        """
        Transforms query results into concise context items.
        """
        projected: List[Dict[str, Any]] = []

        for res in query_results:
            item = res.memory_item
            projected.append({
                "memory_id": item.memory_id,
                "scope": item.scope.value,
                "scope_id": item.scope_id,
                "memory_type": item.memory_type.value,
                "title": item.title,
                "summary": item.summary or item.content[:150],
                "content": item.content,
                "tags": item.tags,
                "score": round(res.score, 2),
            })

        return projected
