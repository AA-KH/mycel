"""
Monitoring profile and watch plan models.

The profile compiler produces a MonitoringProfile from a NetworkArchitecture.
The profile contains the watch plan — an explicit list of WatchTargets that
the scheduler executes directly. The scheduler never needs to "figure out"
what to monitor; it simply runs the watch plan.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from .network import Coordinates, NodeType
from .signals import SignalType
from .state import MonitoringState


class SpatialLogicType(str, Enum):
    """How geographic relevance is determined for a watch target."""

    PROXIMITY_KM = "proximity_km"  # Circle around coordinates
    BUFFER = "buffer"  # Line/corridor buffer (for routes)
    ADMIN_MATCH = "admin_match"  # Country/region administrative match
    GLOBAL = "global"  # Commodity/semantic, no spatial constraint


class SpatialLogic(BaseModel):
    """Spatial matching configuration for a watch target."""

    type: SpatialLogicType
    radius_km: Optional[float] = None  # For PROXIMITY_KM
    buffer_km: Optional[float] = None  # For BUFFER (route corridor width)
    admin_codes: list[str] = Field(default_factory=list)  # ISO3 codes for ADMIN_MATCH


# Default proximity radii by node type — these are starting points, not hard-coded.
DEFAULT_PROXIMITY_KM: dict[NodeType, float] = {
    NodeType.FACTORY: 10.0,
    NodeType.MANUFACTURER: 10.0,
    NodeType.WAREHOUSE: 25.0,
    NodeType.PORT: 15.0,
    NodeType.SUPPLIER: 50.0,
    NodeType.DISTRIBUTOR: 30.0,
    NodeType.RETAILER: 20.0,
    NodeType.HUB: 20.0,
}


class FrequencyPolicy(BaseModel):
    """Polling frequency for a watch target, varies by entity monitoring state."""

    normal_seconds: int = 3600  # 1 hour
    watch_seconds: int = 1800  # 30 min
    elevated_seconds: int = 900  # 15 min
    critical_seconds: int = 300  # 5 min

    def interval_for_state(self, state: MonitoringState) -> int:
        """Return the polling interval in seconds for the given state."""
        return {
            MonitoringState.NORMAL: self.normal_seconds,
            MonitoringState.WATCH: self.watch_seconds,
            MonitoringState.ELEVATED: self.elevated_seconds,
            MonitoringState.CRITICAL: self.critical_seconds,
            MonitoringState.RECOVERY: self.watch_seconds,
        }.get(state, self.normal_seconds)


class WatchTarget(BaseModel):
    """A single monitoring target in the watch plan.

    The scheduler executes WatchTargets directly. Each target knows:
    what to watch, where, through which sources, how often, and why.
    """

    target_id: str
    target_type: str  # entity, location, commodity, route
    entity_id: Optional[str] = None  # Reference to network node
    entity_name: Optional[str] = None
    node_type: Optional[NodeType] = None

    # What signal types to look for
    signal_types: list[SignalType] = Field(default_factory=list)

    # Which sources to use
    sources: list[str] = Field(default_factory=list)

    # Pre-compiled queries for source connectors
    queries: list[str] = Field(default_factory=list)
    query_terms: list[str] = Field(default_factory=list)  # Terms for query composition

    # Geographic context
    coordinates: Optional[Coordinates] = None
    spatial_logic: Optional[SpatialLogic] = None
    countries: list[str] = Field(default_factory=list)  # ISO3

    # Importance
    criticality: float = 0.5  # 0.0-1.0
    dependency_share: Optional[float] = None
    alternate_coverage: Optional[float] = None

    # Scheduling
    frequency: FrequencyPolicy = Field(default_factory=FrequencyPolicy)
    current_state: MonitoringState = MonitoringState.NORMAL

    # Fallbacks
    fallback_sources: list[str] = Field(default_factory=list)


class EntityAlias(BaseModel):
    """Canonical entity with all known name variants."""

    canonical_name: str
    entity_id: str
    aliases: list[str] = Field(default_factory=list)
    abbreviations: list[str] = Field(default_factory=list)
    domain: Optional[str] = None
    country: Optional[str] = None


class QueryGroup(BaseModel):
    """A batched query group that combines related watch requirements.

    Instead of one query per entity, related entities are grouped into
    efficient batched queries where the source supports it.
    """

    group_id: str
    source: str
    query: str
    signal_types: list[SignalType] = Field(default_factory=list)
    entity_ids: list[str] = Field(default_factory=list)
    countries: list[str] = Field(default_factory=list)
    frequency: FrequencyPolicy = Field(default_factory=FrequencyPolicy)
    query_hash: Optional[str] = None  # For deduplication of equivalent queries


class MonitoringProfile(BaseModel):
    """Compiled monitoring profile.

    Produced by the profile compiler from a NetworkArchitecture.
    Contains everything the monitoring system needs to operate.
    """

    profile_id: str
    network_id: str
    architecture_version: str
    compiled_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Entity information
    entity_aliases: list[EntityAlias] = Field(default_factory=list)

    # Location index (coordinates + spatial logic per node)
    watched_coordinates: list[dict] = Field(default_factory=list)
    watched_countries: list[str] = Field(default_factory=list)

    # Commodity watchlist
    watched_commodities: list[str] = Field(default_factory=list)
    commodity_synonyms: dict[str, list[str]] = Field(default_factory=dict)

    # The watch plan — what the scheduler executes
    watch_targets: list[WatchTarget] = Field(default_factory=list)

    # Batched query groups
    query_groups: list[QueryGroup] = Field(default_factory=list)

    # Active sources for this profile
    active_sources: list[str] = Field(default_factory=list)

    # Summary stats
    total_entities: int = 0
    total_locations: int = 0
    total_commodities: int = 0
    total_routes: int = 0
