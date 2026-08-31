"""
Situation and alert models.

Events are grouped into Situations (stable situation_id). Alerts are
attached to situations. New corroborating evidence updates existing
situations rather than creating new alerts. This is the primary
mechanism for preventing alert fatigue.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field

from .state import AlertSeverity, MonitoringState


class RelevanceBreakdown(BaseModel):
    """Multi-dimensional relevance — not one magic number.

    When debugging a false positive, you can see exactly which
    dimensions matched and which didn't.
    """

    entity_match: bool = False
    entity_id: Optional[str] = None
    entity_name: Optional[str] = None

    location_match: bool = False
    location_distance_km: Optional[float] = None
    location_name: Optional[str] = None

    country_match: bool = False
    country_code: Optional[str] = None

    commodity_match: bool = False
    commodity_name: Optional[str] = None

    route_match: bool = False
    route_id: Optional[str] = None

    # From network data — never invented by LLM
    criticality: float = 0.0
    dependency_share: float = 0.0
    alternate_coverage: float = 0.0

    # Event quality
    event_severity: str = "unknown"  # LOW, MEDIUM, HIGH, EXTREME
    source_trust: float = 0.5
    source_count: int = 1

    def has_any_match(self) -> bool:
        """Check if any network dimension matched (for the hard gate)."""
        return any([
            self.entity_match,
            self.location_match,
            self.country_match,
            self.commodity_match,
            self.route_match,
        ])

    def impact_score(self) -> float:
        """Compute overall impact from the dimensional breakdown.

        This is an aggregate convenience score, but the individual
        dimensions are always available for inspection.
        """
        if not self.has_any_match():
            return 0.0

        # Base from strongest match type
        base = 0.0
        if self.entity_match:
            base = max(base, 0.8)
        if self.location_match:
            dist = self.location_distance_km or 999
            if dist < 10:
                base = max(base, 0.7)
            elif dist < 50:
                base = max(base, 0.5)
            else:
                base = max(base, 0.3)
        if self.country_match and not self.entity_match:
            base = max(base, 0.2)
        if self.commodity_match:
            base = max(base, 0.3)
        if self.route_match:
            base = max(base, 0.5)

        # Weight by network importance
        importance = max(self.criticality, self.dependency_share)
        vulnerability = 1.0 - self.alternate_coverage

        score = base * (0.4 + 0.3 * importance + 0.3 * vulnerability)
        return min(1.0, score)


class Situation(BaseModel):
    """A correlated group of events forming a coherent situation.

    Multiple events about the same disruption → one situation.
    Stable situation_id survives new corroborating evidence.
    """

    situation_id: str
    network_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Classification
    title: str
    description: Optional[str] = None
    primary_signal_type: Optional[str] = None

    # Contributing events
    event_ids: list[str] = Field(default_factory=list)
    source_count: int = 0
    independent_source_count: int = 0  # After syndication filtering

    # Affected network elements
    affected_entity_ids: list[str] = Field(default_factory=list)
    affected_locations: list[str] = Field(default_factory=list)
    affected_routes: list[str] = Field(default_factory=list)
    affected_commodities: list[str] = Field(default_factory=list)
    affected_countries: list[str] = Field(default_factory=list)

    # Relevance and confidence
    relevance: Optional[RelevanceBreakdown] = None
    confidence: float = 0.0
    severity: AlertSeverity = AlertSeverity.INFO

    # Evidence path through network graph
    evidence_path: list[str] = Field(default_factory=list)

    # AI interpretation (filled by semantic analyst when invoked)
    ai_interpretation: Optional[str] = None
    why_it_matters: list[str] = Field(default_factory=list)

    # State
    is_active: bool = True
    resolved_at: Optional[datetime] = None

    def add_event(self, event_id: str, source: str) -> None:
        """Add a contributing event to this situation."""
        if event_id not in self.event_ids:
            self.event_ids.append(event_id)
            self.source_count += 1
            self.updated_at = datetime.now(timezone.utc)


class Alert(BaseModel):
    """A structured alert for the main Mycel organization.

    Attached to a situation_id. Contains enough information for the
    main organization to understand what happened without reconstructing
    the monitoring logic. Numerical facts originate from network data.
    """

    alert_id: str
    network_id: str
    situation_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Severity
    severity: AlertSeverity

    # Event information
    event_type: Optional[str] = None
    title: str
    description: Optional[str] = None
    sources: list[dict[str, Any]] = Field(default_factory=list)

    # Affected network elements
    affected_entities: list[dict[str, Any]] = Field(default_factory=list)
    affected_locations: list[str] = Field(default_factory=list)
    affected_routes: list[str] = Field(default_factory=list)
    affected_commodities: list[str] = Field(default_factory=list)

    # Multi-dimensional relevance (full breakdown, not one number)
    relevance: Optional[RelevanceBreakdown] = None
    confidence: float = 0.0

    # Evidence path through network graph
    evidence_path: list[str] = Field(default_factory=list)

    # Human-readable explanations (may be LLM-generated, but facts from data)
    why_it_matters: list[str] = Field(default_factory=list)

    # State transitions caused by this alert
    state_transitions: list[dict[str, str]] = Field(default_factory=list)

    # Dispatch tracking
    dispatched: bool = False
    dispatched_at: Optional[datetime] = None
    dispatch_attempts: int = 0
    idempotency_key: Optional[str] = None
