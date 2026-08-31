"""
Criticality calculator.

Computes criticality scores from network topology data. Numbers come
exclusively from the network architecture — never from an LLM.
"""

from __future__ import annotations

from ..models.network import NetworkArchitecture, NetworkNode, NodeType


def compute_criticality(node: NetworkNode, architecture: NetworkArchitecture) -> float:
    """Compute criticality score for a network node.

    Factors:
    - dependency_share: how much of total supply flows through this node
    - sole_source: whether this is the only supplier for its commodity
    - alternate_capacity: ability of other suppliers to absorb disruption
    - downstream_reach: how many downstream nodes depend on this node
    - node_type: inherent importance (factory > warehouse, etc.)

    Returns a score between 0.0 and 1.0.
    """
    scores: list[float] = []

    # Dependency share (most important factor)
    dep = node.dependency_share or 0.0
    scores.append(dep)

    # Alternate capacity (inverted — less alternate = more critical)
    alt = node.alternate_capacity
    if alt is not None:
        scores.append(1.0 - alt)
    else:
        # Unknown alternate capacity — assume moderate vulnerability
        scores.append(0.5)

    # Sole-source detection: if only one supplier provides a commodity
    if node.type == NodeType.SUPPLIER and node.commodities:
        other_suppliers = [
            n for n in architecture.nodes
            if n.type == NodeType.SUPPLIER
            and n.id != node.id
            and bool(set(n.commodities) & set(node.commodities))
        ]
        if len(other_suppliers) == 0:
            scores.append(1.0)  # Sole source
        else:
            scores.append(0.3)

    # Downstream reach: count nodes reachable from this node
    downstream = _count_downstream(node.id, architecture)
    total_nodes = len(architecture.nodes)
    if total_nodes > 1:
        reach_ratio = downstream / (total_nodes - 1)
        scores.append(min(1.0, reach_ratio * 2))  # Scale up since most nodes connect

    # Node type weight
    type_weights = {
        NodeType.FACTORY: 0.9,
        NodeType.MANUFACTURER: 0.9,
        NodeType.SUPPLIER: 0.7,
        NodeType.PORT: 0.8,
        NodeType.WAREHOUSE: 0.5,
        NodeType.DISTRIBUTOR: 0.4,
        NodeType.HUB: 0.6,
        NodeType.MATERIAL: 0.6,
        NodeType.ROUTE: 0.4,
        NodeType.RETAILER: 0.3,
        NodeType.CUSTOMER: 0.2,
        NodeType.PRODUCT: 0.3,
    }
    scores.append(type_weights.get(node.type, 0.5))

    if not scores:
        return 0.5

    # Weighted average with dependency share getting extra weight
    if node.dependency_share is not None and node.dependency_share > 0:
        return min(1.0, 0.4 * dep + 0.6 * (sum(scores) / len(scores)))
    return min(1.0, sum(scores) / len(scores))


def _count_downstream(node_id: str, architecture: NetworkArchitecture) -> int:
    """Count nodes reachable downstream from the given node. Cycle-safe."""
    visited: set[str] = set()
    queue = [node_id]
    while queue:
        current = queue.pop(0)
        for edge in architecture.edges:
            if edge.source == current and edge.target not in visited:
                visited.add(edge.target)
                queue.append(edge.target)
    return len(visited)
