"""
Profile compiler.

THE CENTRAL INNOVATION: compiles a supply-network architecture into a
dynamic monitoring profile with an explicit watch plan. The supply network
compiles itself into its own monitoring system.

A different network produces different monitoring behavior. The same world
event may be IGNORED by Network A but CRITICAL to Network B.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from ..models.network import (
    Coordinates,
    NetworkArchitecture,
    NetworkNode,
    NodeType,
)
from ..models.profile import (
    DEFAULT_PROXIMITY_KM,
    EntityAlias,
    FrequencyPolicy,
    MonitoringProfile,
    QueryGroup,
    SpatialLogic,
    SpatialLogicType,
    WatchTarget,
)
from ..models.signals import SOURCE_SIGNAL_CAPABILITIES, SignalType
from .criticality import compute_criticality
from .query_builder import build_query_groups


def compile_profile(architecture: NetworkArchitecture) -> MonitoringProfile:
    """Compile a network architecture into a monitoring profile.

    This is the most important function in the system. It determines:
    - WHAT entities matter (with aliases)
    - WHERE to watch (with per-node-type spatial logic)
    - WHAT commodities to track
    - WHICH sources to activate
    - WHAT queries to generate
    - HOW OFTEN to poll each target
    - HOW CRITICAL each node is

    The output is a complete watch plan the scheduler can execute directly.
    """
    profile_id = f"{architecture.network_id}_v{architecture.architecture_version}"

    # ── 1. Build entity alias list ──
    entity_aliases = _build_entity_aliases(architecture)

    # ── 2. Compute criticality for all nodes ──
    criticality_map: dict[str, float] = {}
    for node in architecture.nodes:
        if node.criticality is not None:
            criticality_map[node.id] = node.criticality
        else:
            criticality_map[node.id] = compute_criticality(node, architecture)

    # ── 3. Determine which signal types each node needs ──
    node_signals = _determine_node_signals(architecture)

    # ── 4. Determine which sources to activate ──
    active_sources = _determine_active_sources(node_signals)

    # ── 5. Build watch targets ──
    watch_targets = _build_watch_targets(
        architecture, criticality_map, node_signals, active_sources
    )

    # ── 6. Build query groups (batched, deduplicated) ──
    query_groups: list[QueryGroup] = []
    for source in active_sources:
        query_groups.extend(build_query_groups(watch_targets, source))

    # ── 7. Collect watched data ──
    watched_countries: set[str] = set()
    watched_commodities: set[str] = set()
    watched_hs_codes: set[str] = set()
    watched_coords: list[dict] = []
    total_routes = 0

    for node in architecture.nodes:
        if node.country:
            watched_countries.add(node.country)
        watched_commodities.update(node.commodities)
        watched_hs_codes.update(node.hs_codes)
        if node.coordinates:
            watched_coords.append({
                "node_id": node.id,
                "lat": node.coordinates.latitude,
                "lon": node.coordinates.longitude,
            })
        if node.type == NodeType.ROUTE:
            total_routes += 1

    # Count routes from edges with waypoints
    for edge in architecture.edges:
        if edge.route_waypoints:
            total_routes += 1

    # ── 8. Build commodity synonyms ──
    commodity_synonyms: dict[str, list[str]] = {}
    for node in architecture.nodes:
        if node.type == NodeType.MATERIAL:
            canonical = node.name.lower()
            synonyms = [a.lower() for a in node.aliases if a.lower() != canonical]
            synonyms.extend(c.lower() for c in node.commodities if c.lower() != canonical)
            if synonyms:
                commodity_synonyms[canonical] = list(set(synonyms))

    return MonitoringProfile(
        profile_id=profile_id,
        network_id=architecture.network_id,
        architecture_version=architecture.architecture_version,
        compiled_at=datetime.now(timezone.utc),
        entity_aliases=entity_aliases,
        watched_coordinates=watched_coords,
        watched_countries=sorted(watched_countries),
        watched_commodities=sorted(watched_commodities),
        watched_hs_codes=sorted(watched_hs_codes),
        commodity_synonyms=commodity_synonyms,
        watch_targets=watch_targets,
        query_groups=query_groups,
        active_sources=active_sources,
        total_entities=len([n for n in architecture.nodes if n.type not in (NodeType.MATERIAL, NodeType.PRODUCT)]),
        total_locations=len(watched_coords),
        total_commodities=len(watched_commodities),
        total_routes=total_routes,
    )


def _build_entity_aliases(architecture: NetworkArchitecture) -> list[EntityAlias]:
    """Build canonical entity list with all known name variants."""
    aliases: list[EntityAlias] = []
    for node in architecture.nodes:
        # Skip materials/products — they use commodity matching
        if node.type in (NodeType.MATERIAL, NodeType.PRODUCT):
            continue

        # Build abbreviations from name
        abbreviations = list(node.aliases)  # User-provided aliases
        words = node.name.split()
        if len(words) > 1:
            # Add acronym
            acronym = "".join(w[0].upper() for w in words if w[0].isalpha())
            if len(acronym) >= 2 and acronym not in abbreviations:
                abbreviations.append(acronym)

        aliases.append(EntityAlias(
            canonical_name=node.name,
            entity_id=node.id,
            aliases=node.aliases,
            abbreviations=abbreviations,
            domain=node.domain,
            country=node.country,
        ))
    return aliases


def _determine_node_signals(
    architecture: NetworkArchitecture,
) -> dict[str, list[SignalType]]:
    """Determine which signal types each node should be monitored for."""
    node_signals: dict[str, list[SignalType]] = {}

    for node in architecture.nodes:
        signals: list[SignalType] = []

        if node.type in (NodeType.SUPPLIER, NodeType.MANUFACTURER):
            signals.extend([
                SignalType.SUPPLIER_DISRUPTION,
                SignalType.LABOR_ACTION,
                SignalType.FINANCIAL_DISTRESS,
                SignalType.NATURAL_DISASTER,
                SignalType.WEATHER_HAZARD,
                SignalType.EARTHQUAKE,
            ])
            # International suppliers get trade policy monitoring
            countries = {n.country for n in architecture.nodes if n.country}
            if node.country and len(countries) > 1:
                signals.append(SignalType.TRADE_POLICY)
                signals.append(SignalType.TRADE_RESTRICTION)
                signals.append(SignalType.NON_TARIFF_MEASURE)
                signals.append(SignalType.GEOPOLITICAL)

        elif node.type == NodeType.PORT:
            signals.extend([
                SignalType.PORT_DISRUPTION,
                SignalType.WEATHER_HAZARD,
                SignalType.NATURAL_DISASTER,
                SignalType.EARTHQUAKE,
                SignalType.LABOR_ACTION,
            ])

        elif node.type in (NodeType.FACTORY, NodeType.WAREHOUSE, NodeType.HUB):
            signals.extend([
                SignalType.NATURAL_DISASTER,
                SignalType.WEATHER_HAZARD,
                SignalType.EARTHQUAKE,
                SignalType.INFRASTRUCTURE_DAMAGE,
            ])

        elif node.type == NodeType.MATERIAL:
            signals.extend([
                SignalType.COMMODITY_PRICE,
                SignalType.TRADE_POLICY,
                SignalType.NON_TARIFF_MEASURE,
            ])

        node_signals[node.id] = signals

    return node_signals


def _determine_active_sources(
    node_signals: dict[str, list[SignalType]],
) -> list[str]:
    """Determine which source connectors should be active.

    Only activate sources that can produce signals needed by the network.
    """
    needed_signals: set[SignalType] = set()
    for signals in node_signals.values():
        needed_signals.update(signals)

    active: set[str] = set()
    for source, capabilities in SOURCE_SIGNAL_CAPABILITIES.items():
        if any(sig in needed_signals for sig in capabilities):
            active.add(source)

    # Tier 2 sources — require explicit configuration
    # These are discarded here; they re-appear if the profile compiler
    # selected them AND the registry confirms they are configured.
    active.discard("changedetection")
    active.discard("wto")            # Requires API key
    active.discard("global_trade_alert")  # Requires commercial license
    # WITS is public — no discard needed

    return sorted(active)


def _build_watch_targets(
    architecture: NetworkArchitecture,
    criticality_map: dict[str, float],
    node_signals: dict[str, list[SignalType]],
    active_sources: list[str],
) -> list[WatchTarget]:
    """Build the explicit watch plan.

    Each WatchTarget is a specific monitoring assignment the scheduler
    executes. Per-node-type spatial logic, frequency from criticality.
    """
    targets: list[WatchTarget] = []

    for node in architecture.nodes:
        if node.type in (NodeType.MATERIAL, NodeType.PRODUCT, NodeType.CUSTOMER):
            continue  # These use commodity matching, not entity watching

        signals = node_signals.get(node.id, [])
        if not signals:
            continue

        criticality = criticality_map.get(node.id, 0.5)

        # Determine spatial logic based on node type
        spatial = _spatial_logic_for_node(node)

        # Determine sources for this node's signal needs
        node_sources = []
        for source in active_sources:
            source_caps = SOURCE_SIGNAL_CAPABILITIES.get(source, [])
            if any(sig in source_caps for sig in signals):
                node_sources.append(source)

        # Frequency based on criticality
        frequency = _frequency_for_criticality(criticality)

        # Build query terms for this entity
        query_terms = [node.name] + node.aliases[:3]

        # Collect HS codes from this node and connected material nodes
        node_hs_codes: list[str] = list(node.hs_codes)
        for edge in architecture.edges:
            connected_id = None
            if edge.source == node.id:
                connected_id = edge.target
            elif edge.target == node.id:
                connected_id = edge.source
            if connected_id:
                connected = architecture.get_node(connected_id)
                if connected and connected.type == NodeType.MATERIAL:
                    node_hs_codes.extend(connected.hs_codes)
        node_hs_codes = sorted(set(node_hs_codes))

        target = WatchTarget(
            target_id=f"watch_{node.id}",
            target_type="entity",
            entity_id=node.id,
            entity_name=node.name,
            node_type=node.type,
            signal_types=signals,
            sources=node_sources,
            queries=[],  # Filled by query groups
            query_terms=query_terms,
            hs_codes=node_hs_codes,
            coordinates=node.coordinates,
            spatial_logic=spatial,
            countries=[node.country] if node.country else [],
            criticality=criticality,
            dependency_share=node.dependency_share,
            alternate_coverage=node.alternate_capacity,
            frequency=frequency,
        )
        targets.append(target)

    # Add route-based watch targets from edges with waypoints
    for edge in architecture.edges:
        if not edge.route_waypoints:
            continue
        route_id = f"route_{edge.source}_{edge.target}"
        route_name = edge.metadata.get("route_name", f"{edge.source} → {edge.target}")

        targets.append(WatchTarget(
            target_id=f"watch_{route_id}",
            target_type="route",
            entity_id=route_id,
            entity_name=route_name,
            signal_types=[
                SignalType.ROAD_DISRUPTION,
                SignalType.WEATHER_HAZARD,
                SignalType.NATURAL_DISASTER,
                SignalType.INFRASTRUCTURE_DAMAGE,
            ],
            sources=[s for s in active_sources if s in ("gdelt", "gdacs", "openmeteo", "usgs")],
            coordinates=edge.route_waypoints[0].coordinates if edge.route_waypoints else None,
            spatial_logic=SpatialLogic(
                type=SpatialLogicType.BUFFER,
                buffer_km=30.0,
            ),
            countries=list({
                n.country for n in architecture.nodes
                if n.id in (edge.source, edge.target) and n.country
            }),
            criticality=0.5,
            frequency=FrequencyPolicy(normal_seconds=3600, watch_seconds=1800),
        ))

    return targets


def _spatial_logic_for_node(node: NetworkNode) -> SpatialLogic:
    """Determine spatial matching logic per node type."""
    if node.coordinates:
        radius = DEFAULT_PROXIMITY_KM.get(node.type, 50.0)
        logic = SpatialLogic(
            type=SpatialLogicType.PROXIMITY_KM,
            radius_km=radius,
        )
    elif node.country:
        logic = SpatialLogic(
            type=SpatialLogicType.ADMIN_MATCH,
            admin_codes=[node.country],
        )
    else:
        logic = SpatialLogic(type=SpatialLogicType.GLOBAL)

    # Add country codes for admin matching
    if node.country:
        logic.admin_codes = list(set(logic.admin_codes + [node.country]))

    return logic


def _frequency_for_criticality(criticality: float) -> FrequencyPolicy:
    """Higher criticality → more frequent monitoring."""
    if criticality >= 0.8:
        return FrequencyPolicy(
            normal_seconds=1800, watch_seconds=600,
            elevated_seconds=300, critical_seconds=120,
        )
    elif criticality >= 0.6:
        return FrequencyPolicy(
            normal_seconds=3600, watch_seconds=1200,
            elevated_seconds=600, critical_seconds=180,
        )
    elif criticality >= 0.4:
        return FrequencyPolicy(
            normal_seconds=3600, watch_seconds=1800,
            elevated_seconds=900, critical_seconds=300,
        )
    else:
        return FrequencyPolicy(
            normal_seconds=7200, watch_seconds=3600,
            elevated_seconds=1800, critical_seconds=600,
        )
