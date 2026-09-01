"""
Supply-network architecture schema.

Accepts a directed graph (not DAG). Nodes represent entities in the network
(suppliers, factories, warehouses, ports, routes, etc). Edges represent
directed relationships with dependency information.

All optional fields degrade gracefully — the system works with partial data.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class NodeType(str, Enum):
    """Types of entities in a supply network."""

    SUPPLIER = "supplier"
    MANUFACTURER = "manufacturer"
    FACTORY = "factory"
    WAREHOUSE = "warehouse"
    PORT = "port"
    DISTRIBUTOR = "distributor"
    RETAILER = "retailer"
    CUSTOMER = "customer"
    HUB = "hub"
    MATERIAL = "material"
    PRODUCT = "product"
    ROUTE = "route"


class TransportMode(str, Enum):
    """Transport modes for edges/routes."""

    ROAD = "road"
    RAIL = "rail"
    SEA = "sea"
    AIR = "air"
    PIPELINE = "pipeline"
    MULTIMODAL = "multimodal"


class Coordinates(BaseModel):
    """Geographic coordinates."""

    latitude: float
    longitude: float


class RouteWaypoint(BaseModel):
    """A waypoint along a route with optional metadata."""

    coordinates: Coordinates
    name: Optional[str] = None


class NetworkNode(BaseModel):
    """A node in the supply network graph.

    Represents any entity: supplier, factory, warehouse, port, material, etc.
    Optional fields are genuinely optional — the system degrades gracefully.
    """

    model_config = {"populate_by_name": True}

    id: str
    type: NodeType
    name: str
    aliases: list[str] = Field(default_factory=list)
    location: Optional[str] = None  # City or locality name
    coordinates: Optional[Coordinates] = None
    country: Optional[str] = None  # ISO 3166-1 alpha-3 preferred
    region: Optional[str] = None  # State/province
    criticality: Optional[float] = None  # 0.0-1.0, computed if not provided
    dependency_share: Optional[float] = None  # 0.0-1.0, fraction of total supply
    commodities: list[str] = Field(default_factory=list)
    hs_codes: list[str] = Field(default_factory=list)  # Harmonized System codes for trade monitoring
    alternate_capacity: Optional[float] = None  # 0.0-1.0
    lead_time_days: Optional[float] = None
    website: Optional[str] = None
    domain: Optional[str] = None
    identifiers: dict[str, str] = Field(default_factory=dict)  # e.g. {"duns": "..."}
    metadata: dict[str, str] = Field(default_factory=dict)

    def model_post_init(self, __context: Any) -> None:
        """Migrate legacy metadata.hs_code to first-class hs_codes field."""
        if not self.hs_codes and "hs_code" in self.metadata:
            self.hs_codes = [self.metadata["hs_code"]]


class NetworkEdge(BaseModel):
    """A directed edge in the supply network graph.

    Represents a relationship: supplies, transports, stores, etc.
    The graph is directed but not necessarily acyclic — real supply networks
    can have returns, reverse logistics, and circular flows.
    """

    source: str  # Node ID
    target: str  # Node ID
    relationship: str  # e.g. "supplies", "transports_to", "stores"
    dependency_pct: Optional[float] = None  # 0.0-1.0
    transport_mode: Optional[TransportMode] = None
    route_waypoints: list[RouteWaypoint] = Field(default_factory=list)
    capacity: Optional[float] = None
    lead_time_days: Optional[float] = None
    metadata: dict[str, str] = Field(default_factory=dict)


class NetworkArchitecture(BaseModel):
    """Complete supply-network architecture.

    This is the input contract for the monitoring subsystem. The rest of the
    Mycel system produces this; the monitor consumes it.
    """

    network_id: str
    architecture_version: str = "1"
    name: Optional[str] = None
    description: Optional[str] = None
    nodes: list[NetworkNode]
    edges: list[NetworkEdge]
    metadata: dict[str, str] = Field(default_factory=dict)

    def get_node(self, node_id: str) -> Optional[NetworkNode]:
        """Look up a node by ID."""
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None

    def nodes_by_type(self, node_type: NodeType) -> list[NetworkNode]:
        """Return all nodes of a given type."""
        return [n for n in self.nodes if n.type == node_type]
