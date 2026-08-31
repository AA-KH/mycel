"""
In-memory directed supply-network graph.

NOT a DAG — real supply networks can have cycles (returns, reverse logistics,
circular flows, supplier substitution). All traversal is cycle-safe.

No external graph database. Adjacency lists with indexed metadata.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from ..models.network import NetworkArchitecture, NetworkEdge, NetworkNode


@dataclass
class GraphNode:
    """A node in the supply network graph with adjacency data."""

    node: NetworkNode
    outgoing: list[str] = field(default_factory=list)  # Target node IDs
    incoming: list[str] = field(default_factory=list)  # Source node IDs
    outgoing_edges: list[NetworkEdge] = field(default_factory=list)
    incoming_edges: list[NetworkEdge] = field(default_factory=list)


class NetworkGraph:
    """In-memory directed graph representation of a supply network.

    Supports:
    - Directed edges (not necessarily acyclic)
    - Cycle-safe traversal
    - Downstream impact tracing
    - Upstream dependency tracing
    - Node/edge lookup by ID
    """

    def __init__(self, architecture: NetworkArchitecture):
        self.network_id = architecture.network_id
        self._nodes: dict[str, GraphNode] = {}
        self._edges: list[NetworkEdge] = architecture.edges

        # Build adjacency lists
        for node in architecture.nodes:
            self._nodes[node.id] = GraphNode(node=node)

        for edge in architecture.edges:
            if edge.source in self._nodes:
                self._nodes[edge.source].outgoing.append(edge.target)
                self._nodes[edge.source].outgoing_edges.append(edge)
            if edge.target in self._nodes:
                self._nodes[edge.target].incoming.append(edge.source)
                self._nodes[edge.target].incoming_edges.append(edge)

    def get_node(self, node_id: str) -> Optional[NetworkNode]:
        """Get a network node by ID."""
        graph_node = self._nodes.get(node_id)
        return graph_node.node if graph_node else None

    def all_nodes(self) -> list[NetworkNode]:
        """Return all nodes."""
        return [gn.node for gn in self._nodes.values()]

    def downstream(self, node_id: str) -> list[NetworkNode]:
        """Get immediate downstream nodes."""
        graph_node = self._nodes.get(node_id)
        if not graph_node:
            return []
        return [
            self._nodes[nid].node
            for nid in graph_node.outgoing
            if nid in self._nodes
        ]

    def upstream(self, node_id: str) -> list[NetworkNode]:
        """Get immediate upstream nodes."""
        graph_node = self._nodes.get(node_id)
        if not graph_node:
            return []
        return [
            self._nodes[nid].node
            for nid in graph_node.incoming
            if nid in self._nodes
        ]

    def trace_downstream(self, node_id: str, max_depth: int = 10) -> list[list[str]]:
        """Trace all downstream paths from a node. Cycle-safe.

        Returns a list of paths, where each path is a list of node IDs.
        Used to build evidence paths for alerts.
        """
        paths: list[list[str]] = []
        self._dfs_paths(node_id, [node_id], set(), paths, max_depth)
        return paths

    def _dfs_paths(
        self,
        current: str,
        current_path: list[str],
        visited: set[str],
        all_paths: list[list[str]],
        max_depth: int,
    ) -> None:
        """DFS path enumeration with cycle detection."""
        if len(current_path) > max_depth:
            return

        graph_node = self._nodes.get(current)
        if not graph_node or not graph_node.outgoing:
            if len(current_path) > 1:
                all_paths.append(list(current_path))
            return

        has_unvisited = False
        for neighbor in graph_node.outgoing:
            if neighbor not in visited:
                has_unvisited = True
                visited.add(neighbor)
                current_path.append(neighbor)
                self._dfs_paths(neighbor, current_path, visited, all_paths, max_depth)
                current_path.pop()
                visited.discard(neighbor)

        if not has_unvisited and len(current_path) > 1:
            all_paths.append(list(current_path))

    def trace_upstream(self, node_id: str, max_depth: int = 10) -> list[list[str]]:
        """Trace all upstream paths to a node. Cycle-safe."""
        paths: list[list[str]] = []
        self._dfs_upstream(node_id, [node_id], set(), paths, max_depth)
        return paths

    def _dfs_upstream(
        self,
        current: str,
        current_path: list[str],
        visited: set[str],
        all_paths: list[list[str]],
        max_depth: int,
    ) -> None:
        """Upstream DFS with cycle detection."""
        if len(current_path) > max_depth:
            return

        graph_node = self._nodes.get(current)
        if not graph_node or not graph_node.incoming:
            if len(current_path) > 1:
                all_paths.append(list(reversed(current_path)))
            return

        has_unvisited = False
        for neighbor in graph_node.incoming:
            if neighbor not in visited:
                has_unvisited = True
                visited.add(neighbor)
                current_path.append(neighbor)
                self._dfs_upstream(neighbor, current_path, visited, all_paths, max_depth)
                current_path.pop()
                visited.discard(neighbor)

        if not has_unvisited and len(current_path) > 1:
            all_paths.append(list(reversed(current_path)))

    def dependency_for_edge(self, source_id: str, target_id: str) -> Optional[float]:
        """Get dependency percentage for a specific edge."""
        for edge in self._edges:
            if edge.source == source_id and edge.target == target_id:
                return edge.dependency_pct
        return None

    def edges_from(self, node_id: str) -> list[NetworkEdge]:
        """Get all outgoing edges from a node."""
        graph_node = self._nodes.get(node_id)
        return graph_node.outgoing_edges if graph_node else []


def build_evidence_path(graph: NetworkGraph, affected_node_id: str) -> list[str]:
    """Build human-readable evidence path showing downstream exposure.

    Example: ["Gujarat Graphite Works", "Graphite", "Delhi Pencil Works",
              "Delhi Distribution Centre"]
    """
    paths = graph.trace_downstream(affected_node_id, max_depth=6)
    if not paths:
        node = graph.get_node(affected_node_id)
        return [node.name] if node else [affected_node_id]

    # Take the longest path for the most complete picture
    longest = max(paths, key=len)
    return [
        graph.get_node(nid).name if graph.get_node(nid) else nid
        for nid in longest
    ]
