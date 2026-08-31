"""
Content Library Engine

Tracks all marketing content with status, versioning, and performance linkage.
Provides deduplication, filtering, and lifecycle management.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from teams.marketing.models import (
    ContentAsset, ContentStatus, ContentType, ChannelType,
)

logger = logging.getLogger(__name__)


class ContentLibrary:
    """
    In-process content library for tracking all marketing content.
    
    Provides:
    - Content storage and retrieval
    - Status lifecycle management
    - Campaign-linked content queries
    - Platform-specific content queries
    - Duplication detection
    - Performance linkage
    """

    def __init__(self):
        self._assets: Dict[str, ContentAsset] = {}  # asset_id → ContentAsset

    def store_content(self, asset: ContentAsset) -> ContentAsset:
        """Store a content asset in the library."""
        self._assets[asset.asset_id] = asset
        logger.debug(f"[ContentLibrary] Stored asset {asset.asset_id}: "
                      f"{asset.content_type.value}")
        return asset

    def store_batch(self, assets: List[ContentAsset]) -> List[ContentAsset]:
        """Store multiple content assets."""
        for asset in assets:
            self.store_content(asset)
        return assets

    def get_asset(self, asset_id: str) -> Optional[ContentAsset]:
        """Retrieve a specific content asset."""
        return self._assets.get(asset_id)

    def get_by_campaign(self, campaign_id: str) -> List[ContentAsset]:
        """Get all content assets for a campaign."""
        return [a for a in self._assets.values() if a.campaign_id == campaign_id]

    def get_by_platform(self, platform: ChannelType) -> List[ContentAsset]:
        """Get all content assets for a platform."""
        return [a for a in self._assets.values() if a.platform == platform]

    def get_by_type(self, content_type: ContentType) -> List[ContentAsset]:
        """Get all content assets of a specific type."""
        return [a for a in self._assets.values() if a.content_type == content_type]

    def get_by_status(self, status: ContentStatus) -> List[ContentAsset]:
        """Get all content assets with a specific status."""
        return [a for a in self._assets.values() if a.status == status]

    def get_by_funnel_stage(self, stage) -> List[ContentAsset]:
        """Get all content assets targeting a funnel stage."""
        return [a for a in self._assets.values() if a.funnel_stage == stage]

    def update_status(self, asset_id: str, status: ContentStatus) -> Optional[ContentAsset]:
        """
        Update content status with lifecycle validation.
        
        Valid transitions:
        draft → review → approved → scheduled → published
        draft → review → revision_requested → draft
        any → archived
        any → rejected
        """
        asset = self._assets.get(asset_id)
        if not asset:
            logger.warning(f"[ContentLibrary] Asset {asset_id} not found")
            return None

        valid_transitions = {
            ContentStatus.DRAFT: {ContentStatus.REVIEW, ContentStatus.ARCHIVED, ContentStatus.REJECTED},
            ContentStatus.REVIEW: {ContentStatus.APPROVED, ContentStatus.REVISION_REQUESTED, ContentStatus.REJECTED, ContentStatus.ARCHIVED},
            ContentStatus.REVISION_REQUESTED: {ContentStatus.DRAFT, ContentStatus.ARCHIVED},
            ContentStatus.APPROVED: {ContentStatus.SCHEDULED, ContentStatus.PUBLISHED, ContentStatus.ARCHIVED},
            ContentStatus.SCHEDULED: {ContentStatus.PUBLISHED, ContentStatus.ARCHIVED},
            ContentStatus.PUBLISHED: {ContentStatus.ARCHIVED},
            ContentStatus.REJECTED: {ContentStatus.DRAFT, ContentStatus.ARCHIVED},
            ContentStatus.ARCHIVED: set(),
        }

        allowed = valid_transitions.get(asset.status, set())
        if status not in allowed:
            logger.warning(
                f"[ContentLibrary] Invalid transition: {asset.status.value} → {status.value} "
                f"for asset {asset_id}"
            )
            return None

        asset.status = status
        asset.updated_at = datetime.now(timezone.utc)
        return asset

    def check_duplication(self, topic: str, platform: Optional[ChannelType] = None,
                          threshold: float = 0.7) -> List[ContentAsset]:
        """
        Check for potentially duplicate content by topic similarity.
        Returns assets with similar topics for review.
        """
        topic_lower = topic.lower()
        topic_words = set(topic_lower.split())
        similar = []

        for asset in self._assets.values():
            if platform and asset.platform != platform:
                continue

            asset_topic_lower = asset.topic.lower()
            asset_words = set(asset_topic_lower.split())

            if not asset_words or not topic_words:
                continue

            # Jaccard similarity
            intersection = topic_words & asset_words
            union = topic_words | asset_words
            similarity = len(intersection) / len(union) if union else 0.0

            if similarity >= threshold:
                similar.append(asset)

        return similar

    def get_all(self) -> List[ContentAsset]:
        """Get all content assets."""
        return list(self._assets.values())

    def get_stats(self) -> Dict[str, Any]:
        """Get content library statistics."""
        assets = list(self._assets.values())
        return {
            "total_assets": len(assets),
            "by_status": {
                status.value: len([a for a in assets if a.status == status])
                for status in ContentStatus
            },
            "by_type": {
                ct.value: len([a for a in assets if a.content_type == ct])
                for ct in ContentType
                if any(a.content_type == ct for a in assets)
            },
            "by_platform": {
                ch.value: len([a for a in assets if a.platform == ch])
                for ch in ChannelType
                if any(a.platform == ch for a in assets)
            },
        }

    @property
    def count(self) -> int:
        return len(self._assets)
