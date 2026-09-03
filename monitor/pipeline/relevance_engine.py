"""
Relevance engine.

The technical core. Multi-dimensional relevance scoring with a hard
deterministic gate. Exposes each dimension separately — not one magic number.

Hard gate: no entity + no location + no commodity + no route + no country → REJECT.
This happens BEFORE any LLM call.

Knows: entity exists, entity is in Ahmedabad, entity provides 65%.
Does NOT decide: "does this article describe a shutdown?" (that's the semantic analyst's job)
"""

from __future__ import annotations

from typing import Optional

from loguru import logger

from ..graph.network_graph import NetworkGraph, build_evidence_path
from ..models.events import CanonicalEvent
from ..models.profile import MonitoringProfile
from ..models.situations import RelevanceBreakdown
from .entity_resolver import EntityMatch, EntityResolver
from .geo_matcher import GeoMatch, GeoMatcher


class RelevanceResult:
    """Result of relevance evaluation."""

    def __init__(
        self,
        event: CanonicalEvent,
        breakdown: RelevanceBreakdown,
        passed_gate: bool,
        reject_reason: Optional[str] = None,
        entity_matches: list[EntityMatch] | None = None,
        geo_matches: list[GeoMatch] | None = None,
        needs_semantic_analysis: bool = False,
        evidence_path: list[str] | None = None,
    ):
        self.event = event
        self.breakdown = breakdown
        self.passed_gate = passed_gate
        self.reject_reason = reject_reason
        self.entity_matches = entity_matches or []
        self.geo_matches = geo_matches or []
        self.needs_semantic_analysis = needs_semantic_analysis
        self.evidence_path = evidence_path or []


class RelevanceEngine:
    """Deterministic multi-dimensional relevance scoring.

    Operates on CanonicalEvents using data from the monitoring profile
    and network graph. Every dimension is scored independently.
    """

    def __init__(
        self,
        profile: MonitoringProfile,
        graph: NetworkGraph,
        entity_resolver: EntityResolver,
        geo_matcher: GeoMatcher,
    ):
        self.profile = profile
        self.graph = graph
        self.entity_resolver = entity_resolver
        self.geo_matcher = geo_matcher

        # Build commodity lookup
        self._commodities: set[str] = set()
        for c in profile.watched_commodities:
            self._commodities.add(c.lower())
        for canonical, synonyms in profile.commodity_synonyms.items():
            self._commodities.add(canonical)
            for syn in synonyms:
                self._commodities.add(syn.lower())

    def evaluate(self, event: CanonicalEvent) -> RelevanceResult:
        """Evaluate an event's relevance to the monitored network.

        Returns multi-dimensional breakdown with explicit dimensions.
        Applies the hard deterministic gate.
        """
        breakdown = RelevanceBreakdown()

        # ── 1. Entity matching ──
        entity_matches = self._match_entities(event)
        if entity_matches:
            best = max(entity_matches, key=lambda m: m.confidence)
            breakdown.entity_match = True
            breakdown.entity_id = best.entity_id
            breakdown.entity_name = best.canonical_name
            event.matched_node_ids.append(best.entity_id)
            event.log(f"ENTITY_MATCH: {best.canonical_name} (method={best.method}, conf={best.confidence:.2f})")

            # Populate from network data
            self._populate_network_data(breakdown, best.entity_id)

        # ── 2. Geographic matching ──
        geo_matches = self.geo_matcher.match_event(event)
        if geo_matches:
            best_geo = min(geo_matches, key=lambda m: m.distance_km or float('inf'))
            breakdown.location_match = True
            breakdown.location_distance_km = best_geo.distance_km
            breakdown.location_name = best_geo.entity_name
            event.log(f"GEO_MATCH: {best_geo.entity_name} ({best_geo.match_type}, {best_geo.distance_km or 'admin'})")

            if best_geo.entity_id and not breakdown.entity_match:
                self._populate_network_data(breakdown, best_geo.entity_id)

        # ── 3. Country matching ──
        country_matches = self.geo_matcher.match_country(event)
        if country_matches and not breakdown.location_match:
            best_country = country_matches[0]
            breakdown.country_match = True
            breakdown.country_code = best_country.country_code
            event.log(f"COUNTRY_MATCH: {best_country.country_code}")

            # A country-level event (tariff, sanction, embargo) hits every
            # node in that country. Weight it by the most critical one so the
            # severity policy sees real network importance instead of zeros.
            if not breakdown.entity_match:
                most_critical = self._most_critical_target(
                    [m.entity_id for m in country_matches if m.entity_id]
                )
                if most_critical:
                    self._populate_network_data(breakdown, most_critical)
                    if most_critical not in event.matched_node_ids:
                        event.matched_node_ids.append(most_critical)

        # ── 4. Commodity matching ──
        commodity_match = self._match_commodities(event)
        if commodity_match:
            breakdown.commodity_match = True
            breakdown.commodity_name = commodity_match
            event.log(f"COMMODITY_MATCH: {commodity_match}")

        # ── 5. Route matching ──
        route_matches = [g for g in geo_matches if g.match_type == "route_buffer"]
        if route_matches:
            breakdown.route_match = True
            breakdown.route_id = route_matches[0].target_id
            event.log(f"ROUTE_MATCH: {route_matches[0].entity_name}")

        # ── 6. Event severity from source metadata ──
        breakdown.event_severity = self._classify_event_severity(event)
        breakdown.source_trust = event.source_trust
        breakdown.source_count = 1

        # ── HARD DETERMINISTIC GATE ──
        if not breakdown.has_any_match():
            reject_reason = self._build_reject_reason(event)
            event.log(f"REJECTED: {reject_reason}")
            return RelevanceResult(
                event=event,
                breakdown=breakdown,
                passed_gate=False,
                reject_reason=reject_reason,
                entity_matches=entity_matches,
                geo_matches=geo_matches,
            )

        # ── Build evidence path ──
        evidence_path: list[str] = []
        primary_entity = breakdown.entity_id
        if primary_entity:
            evidence_path = build_evidence_path(self.graph, primary_entity)
        elif geo_matches:
            for gm in geo_matches:
                if gm.entity_id:
                    evidence_path = build_evidence_path(self.graph, gm.entity_id)
                    break

        # ── Determine if semantic analysis is needed ──
        needs_semantic = self._needs_semantic_analysis(event, breakdown, entity_matches)

        event.log(f"RELEVANCE: impact={breakdown.impact_score():.2f}, semantic_needed={needs_semantic}")

        return RelevanceResult(
            event=event,
            breakdown=breakdown,
            passed_gate=True,
            entity_matches=entity_matches,
            geo_matches=geo_matches,
            needs_semantic_analysis=needs_semantic,
            evidence_path=evidence_path,
        )

    def _match_entities(self, event: CanonicalEvent) -> list[EntityMatch]:
        """Match event entities against network."""
        matches: list[EntityMatch] = []

        # Check raw entities
        matches.extend(self.entity_resolver.resolve_many(event.raw_entities))

        # Scan title for entity mentions
        title_matches = self.entity_resolver.scan_text(event.title)
        seen_ids = {m.entity_id for m in matches}
        for m in title_matches:
            if m.entity_id not in seen_ids:
                matches.append(m)
                seen_ids.add(m.entity_id)

        # Scan description if no title matches
        if not matches and event.description:
            desc_matches = self.entity_resolver.scan_text(event.description)
            matches.extend(desc_matches)

        return matches

    def _match_commodities(self, event: CanonicalEvent) -> Optional[str]:
        """Check if event mentions watched commodities."""
        # Check explicit commodities field
        for commodity in event.commodities:
            if commodity.lower() in self._commodities:
                return commodity

        # Scan title for commodity mentions
        title_lower = event.title.lower()
        for commodity in self._commodities:
            if len(commodity) >= 4 and commodity in title_lower:
                return commodity

        return None

    def _most_critical_target(self, entity_ids: list[str]) -> Optional[str]:
        """Return the entity_id with the highest criticality among candidates."""
        best_id: Optional[str] = None
        best_score = -1.0
        wanted = set(entity_ids)
        for target in self.profile.watch_targets:
            if target.entity_id in wanted:
                score = max(target.criticality, target.dependency_share or 0.0)
                if score > best_score:
                    best_score = score
                    best_id = target.entity_id
        return best_id

    def _populate_network_data(self, breakdown: RelevanceBreakdown, entity_id: str) -> None:
        """Populate relevance breakdown with data from the network graph.

        This data comes from the network architecture — never from the LLM.
        """
        for target in self.profile.watch_targets:
            if target.entity_id == entity_id:
                breakdown.criticality = target.criticality
                if target.dependency_share is not None:
                    breakdown.dependency_share = target.dependency_share
                if target.alternate_coverage is not None:
                    breakdown.alternate_coverage = target.alternate_coverage
                break

    def _classify_event_severity(self, event: CanonicalEvent) -> str:
        """Classify event severity from source metadata."""
        meta = event.source_metadata

        # Earthquake magnitude
        mag = meta.get("magnitude")
        if mag is not None:
            if mag >= 7.0:
                return "EXTREME"
            elif mag >= 6.0:
                return "HIGH"
            elif mag >= 5.0:
                return "MEDIUM"
            return "LOW"

        # GDACS alert level
        alert = meta.get("alert_level")
        if alert == "Red":
            return "EXTREME"
        elif alert == "Orange":
            return "HIGH"

        # Weather severity
        precip = meta.get("precipitation_mm")
        wind = meta.get("wind_speed_kmh")
        if precip and precip > 100:
            return "HIGH"
        if wind and wind > 120:
            return "HIGH"

        # Trade policy — export bans/restrictions
        intervention_type = meta.get("intervention_type", "")
        if intervention_type in ("export_ban", "import_ban", "embargo", "sanction"):
            return "HIGH"
        if intervention_type in ("export_restriction", "import_restriction", "quota"):
            return "HIGH"

        # Trade policy — tariff changes
        old_val = meta.get("old_value")
        new_val = meta.get("new_value")
        if old_val is not None and new_val is not None:
            try:
                change = float(new_val) - float(old_val)
                if change > 10:
                    return "HIGH"
                elif change > 0:
                    return "MEDIUM"
                elif change < 0:
                    return "LOW"  # Tariff decrease
            except (ValueError, TypeError):
                pass

        # NTM changes
        ntm_type = meta.get("ntm_type")
        if ntm_type:
            return "MEDIUM"

        # Trade policy — subsidies and state aid
        if intervention_type in ("subsidy", "state_aid", "public_procurement"):
            return "LOW"

        return "MEDIUM"

    def _needs_semantic_analysis(
        self,
        event: CanonicalEvent,
        breakdown: RelevanceBreakdown,
        entity_matches: list[EntityMatch],
    ) -> bool:
        """Determine if this event needs LLM semantic analysis.

        Semantic analysis is needed when:
        - Entity match is fuzzy (needs confirmation)
        - Event comes from unstructured text (GDELT articles)
        - Need to determine if article actually describes a disruption
        - High criticality entity — worth the extra analysis cost

        NOT needed when:
        - Structured data source (USGS, GDACS, Open-Meteo)
        - Already high-confidence structured event
        - No entity match at all (already rejected)
        """
        # Structured sources don't need semantic analysis
        if event.source in ("usgs", "gdacs", "openmeteo", "wto", "global_trade_alert", "wits"):
            return False

        # Fuzzy entity matches need confirmation
        if any(m.method == "fuzzy" for m in entity_matches):
            return True

        # GDELT articles about high-criticality entities need interpretation
        if event.source == "gdelt" and breakdown.criticality >= 0.5:
            return True

        # Text-scanned entity matches with ambiguous context
        if any(m.method == "text_scan" and m.confidence < 0.9 for m in entity_matches):
            return True

        return False

    def _build_reject_reason(self, event: CanonicalEvent) -> str:
        """Build a human-readable reject reason."""
        reasons = []
        reasons.append("No watched entity")
        reasons.append("No matching geography")
        reasons.append("No relevant commodity")

        return "; ".join(reasons)
