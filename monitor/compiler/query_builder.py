"""
Query builder for source connectors.

Builds efficient, batched query groups from watch targets. Related entities
are grouped into shared queries where the source supports boolean operators.
Equivalent queries are hash-deduplicated.
"""

from __future__ import annotations

import hashlib
from typing import Optional

from ..models.network import NodeType
from ..models.profile import FrequencyPolicy, QueryGroup
from ..models.signals import SignalType


# Disruption keywords by signal type
DISRUPTION_KEYWORDS: dict[SignalType, list[str]] = {
    SignalType.SUPPLIER_DISRUPTION: [
        "shutdown", "closure", "closed", "fire", "explosion", "bankruptcy",
        "insolvent", "strike", "labor dispute", "production halt",
        "operations suspended", "factory fire", "plant closure",
    ],
    SignalType.PORT_DISRUPTION: [
        "port closure", "port congestion", "shipping delay", "dock strike",
        "port shutdown", "vessel delay", "container shortage",
    ],
    SignalType.ROAD_DISRUPTION: [
        "road closure", "highway blocked", "landslide", "road damage",
        "bridge collapse", "traffic disruption", "transport delay",
    ],
    SignalType.TRADE_POLICY: [
        "tariff", "sanction", "export ban", "import restriction",
        "trade war", "customs duty", "trade policy",
    ],
    SignalType.GEOPOLITICAL: [
        "conflict", "political crisis", "government instability",
        "coup", "civil unrest", "protests", "military",
    ],
    SignalType.REGULATORY: [
        "regulation", "compliance", "regulatory change", "new law",
        "environmental regulation", "safety regulation",
    ],
    SignalType.LABOR_ACTION: [
        "strike", "walkout", "labor dispute", "union action",
        "workers protest", "industrial action",
    ],
    SignalType.FINANCIAL_DISTRESS: [
        "bankruptcy", "debt default", "financial trouble",
        "credit downgrade", "insolvency", "liquidation",
    ],
}

# Keywords relevant to node types
NODE_TYPE_KEYWORDS: dict[NodeType, list[str]] = {
    NodeType.SUPPLIER: ["supplier", "manufacturer", "production", "factory", "plant"],
    NodeType.PORT: ["port", "harbor", "terminal", "shipping", "cargo"],
    NodeType.FACTORY: ["factory", "plant", "manufacturing", "production"],
    NodeType.WAREHOUSE: ["warehouse", "storage", "distribution center"],
}


def build_gdelt_query(
    entity_names: list[str],
    signal_type: SignalType,
    countries: Optional[list[str]] = None,
) -> str:
    """Build a GDELT DOC API query string.

    Groups entities with OR and combines with disruption keywords.
    Example: ("Gujarat Graphite" OR "Deutsche Holz") (shutdown OR fire OR bankruptcy)
    """
    if not entity_names:
        return ""

    # Entity part: quoted names joined with OR
    entity_parts = [f'"{name}"' for name in entity_names[:5]]  # Cap at 5 per query
    entity_clause = f"({' OR '.join(entity_parts)})"

    # Disruption keywords for this signal type
    keywords = DISRUPTION_KEYWORDS.get(signal_type, [])
    if not keywords:
        return entity_clause

    # Take top keywords to keep query manageable
    keyword_parts = keywords[:6]
    keyword_clause = f"({' OR '.join(keyword_parts)})"

    query = f"{entity_clause} {keyword_clause}"

    # Optional country filter
    if countries:
        country_clause = f"sourcecountry:{'|'.join(countries[:3])}"
        query = f"{query} {country_clause}"

    return query


def build_query_groups(
    watch_targets: list,
    source: str = "gdelt",
) -> list[QueryGroup]:
    """Build deduplicated query groups from watch targets.

    Combines related watch targets into efficient batched queries.
    Hash-deduplicates equivalent queries.

    Trade sources (wto, global_trade_alert, wits) use structured
    parameters (countries + HS codes). Text-based sources (gdelt) use
    keyword queries.
    """
    # Route trade sources to structured builder
    if source in ("wto", "global_trade_alert", "wits"):
        return _build_trade_query_groups(watch_targets, source)

    # Group watch targets by signal type
    by_signal: dict[SignalType, list] = {}
    for target in watch_targets:
        if source not in target.sources:
            continue
        for sig in target.signal_types:
            by_signal.setdefault(sig, []).append(target)

    groups: list[QueryGroup] = []
    seen_hashes: set[str] = set()

    for signal_type, targets in by_signal.items():
        # Collect entity names and countries from targets
        entity_names = []
        entity_ids = []
        countries = set()
        for t in targets:
            if t.entity_name:
                entity_names.append(t.entity_name)
            if t.entity_id:
                entity_ids.append(t.entity_id)
            countries.update(t.countries)

        if not entity_names:
            continue

        # Build query
        query = build_gdelt_query(
            entity_names=entity_names,
            signal_type=signal_type,
            countries=list(countries) if countries else None,
        )

        # Hash for deduplication
        query_hash = hashlib.sha256(query.encode()).hexdigest()[:16]
        if query_hash in seen_hashes:
            continue
        seen_hashes.add(query_hash)

        # Use highest criticality frequency from contributing targets
        min_normal = min(t.frequency.normal_seconds for t in targets)

        group = QueryGroup(
            group_id=f"{source}_{signal_type.value}_{query_hash[:8]}",
            source=source,
            query=query,
            signal_types=[signal_type],
            entity_ids=entity_ids,
            countries=list(countries),
            frequency=FrequencyPolicy(normal_seconds=min_normal),
            query_hash=query_hash,
        )
        groups.append(group)

    return groups


def _build_trade_query_groups(
    watch_targets: list,
    source: str,
) -> list[QueryGroup]:
    """Build query groups for trade sources using structured parameters.

    Trade sources (WTO, GTA, WITS) use countries + HS codes, not text queries.
    Groups targets by country set to minimize API calls.
    """
    # Collect all countries and HS codes from targets that use this source
    all_countries: set[str] = set()
    all_hs_codes: set[str] = set()
    all_entity_ids: list[str] = []
    all_signal_types: set[SignalType] = set()
    targets_for_source = []

    for target in watch_targets:
        if source not in target.sources:
            continue
        targets_for_source.append(target)
        all_countries.update(target.countries)
        all_hs_codes.update(getattr(target, "hs_codes", []))
        if target.entity_id:
            all_entity_ids.append(target.entity_id)
        all_signal_types.update(target.signal_types)

    if not targets_for_source or not all_countries:
        return []

    # Filter to trade-relevant signal types
    trade_signals = [
        s for s in all_signal_types
        if s in (
            SignalType.TRADE_POLICY,
            SignalType.TRADE_RESTRICTION,
            SignalType.NON_TARIFF_MEASURE,
            SignalType.REGULATORY,
            SignalType.GEOPOLITICAL,
        )
    ]
    if not trade_signals:
        return []

    # Build a single consolidated query group per source
    # Trade sources handle their own internal iteration over countries/HS codes
    countries = sorted(all_countries)
    hs_codes = sorted(all_hs_codes)

    # Query descriptor (not a text query — just metadata for logging)
    query_desc = f"trade:{source}|countries={','.join(countries[:5])}|hs={','.join(hs_codes[:5])}"
    query_hash = hashlib.sha256(query_desc.encode()).hexdigest()[:16]

    min_normal = min(t.frequency.normal_seconds for t in targets_for_source)

    group = QueryGroup(
        group_id=f"{source}_trade_{query_hash[:8]}",
        source=source,
        query=query_desc,
        signal_types=trade_signals,
        entity_ids=all_entity_ids,
        countries=countries,
        hs_codes=hs_codes,
        frequency=FrequencyPolicy(normal_seconds=min_normal),
        query_hash=query_hash,
    )

    return [group]

