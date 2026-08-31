"""
Memory Service (Phase 12 Memory System Facade)

Responsibilities:
- Coordinates memory recording, extraction, validation, storage, indexing, retrieval, and context projection.
- Strict Invariants:
    - Memory is NOT Knowledge (curated manual).
    - Memory is NOT Chat History (raw transcripts).
    - Memory is NOT Artifact Storage (deliverable binaries).
    - Memory is NOT Context (temporary runtime view).
"""

import logging
from typing import List, Dict, Any, Optional, Tuple

from memory.models import (
    MemoryItem,
    MemoryScope,
    MemoryType,
    MemoryImportance,
    MemoryQueryResult,
    MemoryExtractRequest,
)
from memory.validator import MemoryValidator
from memory.extractor import MemoryExtractor
from memory.store import MemoryStore
from memory.indexer import MemoryIndexer
from memory.retriever import MemoryRetriever
from memory.projector import MemoryContextProjector

logger = logging.getLogger(__name__)


class MemoryService:
    """
    Facade service orchestrating Memory System operations.
    """

    def __init__(self, store: Optional[MemoryStore] = None):
        self._store = store or MemoryStore()
        self._indexer = MemoryIndexer()
        self._validator = MemoryValidator()
        self._extractor = MemoryExtractor()
        self._retriever = MemoryRetriever(self._store, self._indexer)
        self._projector = MemoryContextProjector()

    def record_memory(self, item: MemoryItem) -> Tuple[Optional[MemoryItem], List[str]]:
        """
        Validates, persists, and indexes a MemoryItem.
        Returns (saved_item, errors).
        """
        valid, errors = self._validator.validate_memory(item)
        if not valid:
            logger.warning(f"Memory validation failed for '{item.memory_id}': {errors}")
            return None, errors

        saved = self._store.save(item)
        self._indexer.index_item(saved)
        return saved, []

    def extract_and_record(self, request: MemoryExtractRequest) -> Tuple[Optional[MemoryItem], List[str]]:
        """
        Extracts structured MemoryItem from request, validates, and persists it.
        """
        item = self._extractor.extract_memory(request)
        return self.record_memory(item)

    def query_memories(
        self,
        scope: MemoryScope,
        scope_id: str,
        keywords: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        min_importance: Optional[MemoryImportance] = None,
        limit: int = 5,
    ) -> List[MemoryQueryResult]:
        """
        Queries active memories for a given scope, ranked by relevance.
        """
        return self._retriever.query_memories(
            scope=scope,
            scope_id=scope_id,
            keywords=keywords,
            tags=tags,
            min_importance=min_importance,
            limit=limit,
        )

    def get_context_memories(
        self,
        scope: MemoryScope,
        scope_id: str,
        keywords: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Retrieves relevant memories and projects them into minimal context dictionary.
        """
        query_results = self.query_memories(scope, scope_id, keywords, tags, limit=limit)
        return self._projector.project_memories_to_context(query_results)

    def supersede_memory(
        self, old_memory_id: str, new_item: MemoryItem
    ) -> Tuple[Optional[MemoryItem], List[str]]:
        """
        Supersedes an existing memory item with a new updated memory item.
        """
        valid, errors = self._validator.validate_memory(new_item)
        if not valid:
            return None, errors

        old_item = self._store.supersede(old_memory_id, new_item)
        if not old_item:
            return None, [f"Old MemoryItem '{old_memory_id}' not found."]

        self._indexer.index_item(new_item)
        return new_item, []

    def archive_memory(self, memory_id: str) -> bool:
        """Archives a memory item."""
        archived = self._store.archive(memory_id)
        if archived:
            self._indexer.remove_item(memory_id)
        return archived

    def get_memory(self, memory_id: str) -> Optional[MemoryItem]:
        return self._store.get(memory_id)
