"""
Brand Memory Engine

Manages brand context persistence using the Mycel MemoryService.
Stores brand identity, positioning, messaging, audience, and learnings
so the Marketing Team has consistent context across tasks.

Uses:
- MemoryScope.TEAM with scope_id="marketing"
- MemoryType.SEMANTIC for brand facts
- MemoryType.EPISODIC for campaign history
- MemoryType.LESSON for performance learnings
"""

import json
import logging
from typing import Optional, List, Dict, Any

from teams.marketing.models import BrandContext, ChannelType

logger = logging.getLogger(__name__)


class BrandMemoryEngine:
    """
    Brand context management — in-process storage with MemoryService integration.
    
    In the initial implementation, brand context is stored in-process.
    When the MemoryService is connected, it persists to MongoDB via
    the existing memory infrastructure.
    """

    def __init__(self):
        self._brand_context: Optional[BrandContext] = None
        self._campaign_history: List[Dict[str, Any]] = []
        self._learnings: List[str] = []
        self._content_history: List[Dict[str, Any]] = []
        self._memory_service = None

        # Try to connect to MemoryService
        try:
            from memory.service import MemoryService
            self._memory_service = MemoryService()
        except Exception as e:
            logger.debug(f"[BrandMemory] MemoryService not available: {e}")

    def load_brand_context(self) -> Optional[BrandContext]:
        """
        Load the current brand context.
        First checks in-process cache, then MemoryService.
        """
        if self._brand_context:
            return self._brand_context

        # Try loading from MemoryService
        if self._memory_service:
            try:
                from memory.models import MemoryScope, MemoryType
                results = self._memory_service.query_memories(
                    scope=MemoryScope.TEAM,
                    scope_id="marketing",
                    tags=["brand_context"],
                    limit=1,
                )
                if results:
                    content = results[0].memory_item.content
                    data = json.loads(content)
                    self._brand_context = BrandContext(**data)
                    logger.info("[BrandMemory] Loaded brand context from MemoryService")
                    return self._brand_context
            except Exception as e:
                logger.debug(f"[BrandMemory] Could not load from MemoryService: {e}")

        return None

    def save_brand_context(self, brand_context: BrandContext) -> None:
        """
        Save brand context to in-process cache and MemoryService.
        """
        self._brand_context = brand_context

        if self._memory_service:
            try:
                from memory.models import (
                    MemoryItem, MemoryScope, MemoryType, MemoryImportance
                )
                import uuid

                item = MemoryItem(
                    memory_id=f"brand_ctx_{uuid.uuid4().hex[:8]}",
                    scope=MemoryScope.TEAM,
                    scope_id="marketing",
                    memory_type=MemoryType.SEMANTIC,
                    importance=MemoryImportance.HIGH,
                    title=f"Brand Context: {brand_context.name or 'Current Brand'}",
                    content=brand_context.model_dump_json(),
                    summary=f"Brand context for {brand_context.name}",
                    tags=["brand_context", "brand_identity"],
                    source_team_id="marketing",
                )
                self._memory_service.record_memory(item)
                logger.info("[BrandMemory] Saved brand context to MemoryService")
            except Exception as e:
                logger.debug(f"[BrandMemory] Could not save to MemoryService: {e}")

    def update_brand_learnings(self, campaign_id: str, learnings: List[str]) -> None:
        """Store performance learnings from a campaign."""
        self._learnings.extend(learnings)

        if self._brand_context:
            self._brand_context.learnings.extend(learnings)
            # Keep only the most recent learnings
            self._brand_context.learnings = self._brand_context.learnings[-50:]

        if self._memory_service:
            try:
                from memory.models import (
                    MemoryItem, MemoryScope, MemoryType, MemoryImportance
                )
                import uuid

                item = MemoryItem(
                    memory_id=f"learning_{uuid.uuid4().hex[:8]}",
                    scope=MemoryScope.TEAM,
                    scope_id="marketing",
                    memory_type=MemoryType.LESSON,
                    importance=MemoryImportance.MEDIUM,
                    title=f"Campaign Learnings: {campaign_id}",
                    content=json.dumps(learnings),
                    summary=f"Learnings from campaign {campaign_id}",
                    tags=["campaign_learning", campaign_id],
                    source_team_id="marketing",
                )
                self._memory_service.record_memory(item)
            except Exception as e:
                logger.debug(f"[BrandMemory] Could not save learnings: {e}")

    def record_campaign(self, campaign_summary: Dict[str, Any]) -> None:
        """Record a completed campaign for historical reference."""
        self._campaign_history.append(campaign_summary)

        if self._brand_context:
            campaign_id = campaign_summary.get("campaign_id", "unknown")
            if campaign_id not in self._brand_context.historical_campaigns:
                self._brand_context.historical_campaigns.append(campaign_id)

    def record_content(self, content_summary: Dict[str, Any]) -> None:
        """Record published content for deduplication and history."""
        self._content_history.append(content_summary)

    def get_campaign_history(self) -> List[Dict[str, Any]]:
        """Retrieve past campaign summaries."""
        return self._campaign_history

    def get_content_history(self, platform: Optional[str] = None,
                            topic: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve published content history, optionally filtered."""
        results = self._content_history
        if platform:
            results = [c for c in results if c.get("platform") == platform]
        if topic:
            results = [c for c in results if topic.lower() in c.get("topic", "").lower()]
        return results

    def get_learnings(self, limit: int = 20) -> List[str]:
        """Retrieve the most recent learnings."""
        return self._learnings[-limit:]
