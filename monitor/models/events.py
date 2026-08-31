"""
Canonical event envelope.

Every source normalizes into this common schema. Downstream processing
operates on CanonicalEvent instances, never on raw source data. The
signal_type field is the primary classifier — source identity is metadata.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field

from .signals import SignalType


class EventLocation(BaseModel):
    """A location mentioned in or associated with an event."""

    name: Optional[str] = None
    country: Optional[str] = None  # ISO3
    country_name: Optional[str] = None
    region: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class CanonicalEvent(BaseModel):
    """Universal event envelope.

    Every source connector normalizes its raw data into this schema.
    All downstream processing operates on CanonicalEvent instances.
    """

    # Identity
    event_id: str  # Internal unique ID (generated)
    source: str  # Source connector name
    source_event_id: Optional[str] = None  # Original ID from source
    source_url: Optional[str] = None

    # Timing
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    event_time: Optional[datetime] = None  # When the event actually occurred

    # Classification
    signal_type: SignalType
    event_type: Optional[str] = None  # More specific sub-type

    # Content
    title: str
    description: Optional[str] = None

    # Extracted entities and locations
    raw_entities: list[str] = Field(default_factory=list)
    locations: list[EventLocation] = Field(default_factory=list)
    countries: list[str] = Field(default_factory=list)  # ISO3 codes
    commodities: list[str] = Field(default_factory=list)

    # Network matching (populated by relevance engine)
    matched_node_ids: list[str] = Field(default_factory=list)

    # Deduplication
    content_hash: Optional[str] = None
    title_hash: Optional[str] = None
    dedup_of: Optional[str] = None  # If this is a duplicate, reference original

    # Trust and quality
    confidence: float = 0.5  # 0.0-1.0
    source_trust: float = 0.5  # 0.0-1.0

    # Profile context
    profile_id: Optional[str] = None
    network_id: Optional[str] = None

    # Source-specific metadata (extensible without schema changes)
    source_metadata: dict[str, Any] = Field(default_factory=dict)

    # Processing trace
    processing_log: list[str] = Field(default_factory=list)

    def log(self, message: str) -> None:
        """Append to processing trace for observability."""
        self.processing_log.append(
            f"{datetime.now(timezone.utc).isoformat()} {message}"
        )
