"""
Memory Store (Phase 12 Memory System)

Responsibilities:
- Thread-safe in-memory storage & repository interface for MemoryItems.
- Supports CRUD operations, scope filtering, status transitions, and memory superseding.
"""

import threading
import logging
from typing import Dict, List, Optional
from datetime import datetime, timezone

from memory.models import MemoryItem, MemoryScope, MemoryStatus

logger = logging.getLogger(__name__)


class MemoryStore:
    """
    Thread-safe repository for MemoryItem records.
    """

    def __init__(self):
        self._lock = threading.RLock()
        self._items: Dict[str, MemoryItem] = {}

    def save(self, item: MemoryItem) -> MemoryItem:
        with self._lock:
            item.updated_at = datetime.now(timezone.utc)
            self._items[item.memory_id] = item
            logger.info(f"Saved MemoryItem '{item.memory_id}' under scope {item.scope.value}:{item.scope_id}")
            return item

    def get(self, memory_id: str) -> Optional[MemoryItem]:
        with self._lock:
            return self._items.get(memory_id)

    def list_all(self) -> List[MemoryItem]:
        with self._lock:
            return list(self._items.values())

    def list_by_scope(self, scope: MemoryScope, scope_id: str) -> List[MemoryItem]:
        with self._lock:
            return [
                item for item in self._items.values()
                if item.scope == scope and item.scope_id == scope_id
            ]

    def list_active_by_scope(self, scope: MemoryScope, scope_id: str) -> List[MemoryItem]:
        with self._lock:
            return [
                item for item in self._items.values()
                if item.scope == scope and item.scope_id == scope_id and item.is_active
            ]

    def supersede(self, old_memory_id: str, new_item: MemoryItem) -> Optional[MemoryItem]:
        """
        Marks old_memory_id as SUPERSEDED and links it to new_item.
        """
        with self._lock:
            old_item = self._items.get(old_memory_id)
            if not old_item:
                return None

            # Save new item first
            self.save(new_item)

            # Update old item status
            old_item.status = MemoryStatus.SUPERSEDED
            old_item.superseded_by = new_item.memory_id
            old_item.updated_at = datetime.now(timezone.utc)

            logger.info(f"MemoryItem '{old_memory_id}' superseded by '{new_item.memory_id}'")
            return old_item

    def archive(self, memory_id: str) -> bool:
        with self._lock:
            item = self._items.get(memory_id)
            if not item:
                return False
            item.status = MemoryStatus.ARCHIVED
            item.updated_at = datetime.now(timezone.utc)
            return True

    def delete(self, memory_id: str) -> bool:
        with self._lock:
            if memory_id in self._items:
                del self._items[memory_id]
                return True
            return False

    def count(self) -> int:
        with self._lock:
            return len(self._items)
