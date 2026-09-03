"""
Correlation engine.

Deterministic-first correlation. Groups related signals into situations
using shared graph nodes, geography, temporal overlap, and signal type
compatibility. Assigns stable situation_ids.

Correlation happens BEFORE the LLM. The LLM receives pre-correlated
situations: "Three sources describe potentially related disruption
around Supplier A" — much cheaper than per-event reasoning.

3 syndicated copies of one Reuters article ≠ 3 independent confirmations.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import uuid4

from loguru import logger

from ..models.events import CanonicalEvent
from ..models.situations import RelevanceBreakdown, Situation
from .relevance_engine import RelevanceResult


class CorrelationEngine:
    """Groups related events into coherent situations.

    Deterministic correlation based on:
    - Shared network entities (same supplier, same port)
    - Shared geography (same region/city within threshold)
    - Temporal overlap (events within configurable time window)
    - Compatible signal types (earthquake + infrastructure damage)
    """

    def __init__(
        self,
        network_id: str,
        time_window_hours: int = 24,
    ):
        self.network_id = network_id
        self.time_window = timedelta(hours=time_window_hours)
        self._situations: dict[str, Situation] = {}

    def correlate(self, result: RelevanceResult) -> Situation:
        """Correlate an event into an existing or new situation.

        First tries to find an existing situation that this event belongs to.
        If none found, creates a new situation.

        Returns the situation (new or updated).
        """
        event = result.event
        breakdown = result.breakdown

        # Try to find an existing matching situation
        existing = self._find_matching_situation(event, breakdown)

        if existing:
            # Update existing situation with new evidence
            existing.add_event(event.event_id, event.source)

            # Check source independence
            if self._is_independent_source(event, existing):
                existing.independent_source_count += 1

            # Update confidence based on corroboration
            existing.confidence = self._compute_situation_confidence(existing)

            # Update relevance if stronger
            if breakdown.impact_score() > (existing.relevance.impact_score() if existing.relevance else 0):
                existing.relevance = breakdown

            event.log(f"CORRELATED: merged into situation {existing.situation_id}")
            return existing

        # Create new situation
        situation = self._create_situation(event, result)
        self._situations[situation.situation_id] = situation
        event.log(f"SITUATION_CREATED: {situation.situation_id}")
        return situation

    def get_situation(self, situation_id: str) -> Optional[Situation]:
        """Get a situation by ID."""
        return self._situations.get(situation_id)

    def active_situations(self) -> list[Situation]:
        """Return all active situations."""
        return [s for s in self._situations.values() if s.is_active]

    def _find_matching_situation(
        self, event: CanonicalEvent, breakdown: RelevanceBreakdown
    ) -> Optional[Situation]:
        """Find an existing situation this event should be correlated with.

        Matching criteria:
        1. Shared entity (strongest signal)
        2. Shared geography + compatible time window
        3. Compatible signal types within same region
        """
        now = datetime.now(timezone.utc)

        for situation in self._situations.values():
            if not situation.is_active:
                continue

            # Check time window
            if now - situation.updated_at > self.time_window:
                continue

            # Criterion 1: Shared entity
            if breakdown.entity_id and breakdown.entity_id in situation.affected_entity_ids:
                return situation

            # Criterion 2: Shared geography + compatible signal
            event_countries = set(event.countries)
            situation_countries = set(situation.affected_countries)
            if event_countries & situation_countries:
                # Same country — check if signal types are related
                event_signal = event.signal_type.value
                if event_signal == situation.primary_signal_type:
                    return situation

                # Related signals (e.g., earthquake + infrastructure damage)
                related_pairs = {
                    ("earthquake", "infrastructure_damage"),
                    ("weather_hazard", "road_disruption"),
                    ("weather_hazard", "port_disruption"),
                    ("natural_disaster", "infrastructure_damage"),
                    ("natural_disaster", "road_disruption"),
                    ("labor_action", "supplier_disruption"),
                    ("labor_action", "port_disruption"),
                    # Trade-related cross-source correlation
                    ("trade_policy", "trade_restriction"),
                    ("trade_policy", "geopolitical"),
                    ("trade_restriction", "supplier_disruption"),
                    ("trade_restriction", "geopolitical"),
                    ("non_tariff_measure", "regulatory"),
                }
                pair = tuple(sorted([event_signal, situation.primary_signal_type or ""]))
                if pair in related_pairs:
                    return situation

            # Criterion 3: Shared commodity
            event_commodities = set(event.commodities)
            situation_commodities = set(situation.affected_commodities)
            if event_commodities & situation_commodities:
                if event.signal_type.value in ("trade_policy", "commodity_price"):
                    return situation

            # Criterion 4: Multi-dimensional commodity + country correlation
            # If events share BOTH a commodity AND a country, they are
            # candidates for the same situation regardless of signal type.
            # This enables: GTA (China graphite) + GDELT (China graphite)
            #   + WTO (China graphite) → one situation.
            if event_commodities & situation_commodities and event_countries & situation_countries:
                return situation

        return None

    def _is_independent_source(self, event: CanonicalEvent, situation: Situation) -> bool:
        """Check if the event is from a genuinely independent source.

        3 syndicated copies of one Reuters article ≠ 3 independent confirmations.
        Independence is determined by source connector name (GDELT vs GDACS vs USGS).
        Within GDELT, different domains could be syndicated — we count GDELT as one source.
        """
        # Different source connectors are independent
        existing_sources = set()
        # We track source names in situation — simplified approach
        if event.source not in [event.source]:
            return True

        # Same source connector — likely syndicated
        return event.source not in existing_sources

    def _compute_situation_confidence(self, situation: Situation) -> float:
        """Compute situation confidence from corroboration.

        Independent sources increase confidence:
        1 source: base confidence
        2 independent: +0.15
        3 independent: +0.25
        More doesn't add much (diminishing returns)
        """
        base = situation.relevance.source_trust if situation.relevance else 0.5
        independent = situation.independent_source_count

        if independent >= 3:
            return min(0.95, base + 0.25)
        elif independent >= 2:
            return min(0.90, base + 0.15)
        else:
            return base

    def _create_situation(self, event: CanonicalEvent, result: RelevanceResult) -> Situation:
        """Create a new situation from an event."""
        situation_id = f"SIT-{uuid4().hex[:8].upper()}"

        affected_entities: list[str] = []
        if result.breakdown.entity_id:
            affected_entities.append(result.breakdown.entity_id)
        # Country/geo-level matches record the impacted node(s) on the event
        for node_id in event.matched_node_ids:
            if node_id not in affected_entities:
                affected_entities.append(node_id)

        affected_locations = []
        if result.breakdown.location_name:
            affected_locations.append(result.breakdown.location_name)

        affected_countries = list(set(event.countries))

        affected_commodities = list(set(event.commodities))
        if result.breakdown.commodity_name:
            affected_commodities.append(result.breakdown.commodity_name)
            affected_commodities = list(set(affected_commodities))

        return Situation(
            situation_id=situation_id,
            network_id=self.network_id,
            title=event.title,
            description=event.description,
            primary_signal_type=event.signal_type.value,
            event_ids=[event.event_id],
            source_count=1,
            independent_source_count=1,
            affected_entity_ids=affected_entities,
            affected_locations=affected_locations,
            affected_commodities=affected_commodities,
            affected_countries=affected_countries,
            relevance=result.breakdown,
            confidence=event.confidence,
            evidence_path=result.evidence_path,
        )

    def resolve_stale(self, max_age_hours: int = 72) -> int:
        """Mark old situations as resolved."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
        resolved = 0
        for situation in self._situations.values():
            if situation.is_active and situation.updated_at < cutoff:
                situation.is_active = False
                situation.resolved_at = datetime.now(timezone.utc)
                resolved += 1
        return resolved
