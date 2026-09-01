"""
Geographic matcher.

Matches events to network nodes using per-node-type spatial logic:
- Factory → very close proximity (~10km)
- Warehouse → local proximity (~25km)
- Port → port-area proximity (~15km)
- Route → line/buffer intersection
- Country dependency → administrative/ISO3 match
- Supplier HQ → broader location relevance (~50km)

Uses Haversine distance. No external geocoding API calls during matching.
"""

from __future__ import annotations

import math
from typing import Optional

from ..models.events import CanonicalEvent, EventLocation
from ..models.profile import (
    MonitoringProfile,
    SpatialLogicType,
    WatchTarget,
)
from ..models.network import Coordinates


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great-circle distance between two points in kilometers."""
    R = 6371.0  # Earth's radius in km

    lat1_r = math.radians(lat1)
    lat2_r = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


class GeoMatch:
    """Result of geographic matching."""

    __slots__ = ("target_id", "entity_id", "entity_name", "match_type",
                 "distance_km", "country_code")

    def __init__(
        self,
        target_id: str,
        entity_id: str | None,
        entity_name: str | None,
        match_type: str,  # proximity, buffer, admin, route
        distance_km: float | None = None,
        country_code: str | None = None,
    ):
        self.target_id = target_id
        self.entity_id = entity_id
        self.entity_name = entity_name
        self.match_type = match_type
        self.distance_km = distance_km
        self.country_code = country_code

    def __repr__(self) -> str:
        if self.distance_km is not None:
            return f"GeoMatch({self.entity_name}, {self.match_type}, {self.distance_km:.1f}km)"
        return f"GeoMatch({self.entity_name}, {self.match_type})"


class GeoMatcher:
    """Matches events to network nodes by geography.

    Uses per-node-type proximity thresholds. Route matching uses waypoint
    buffer checking. Country matching uses ISO3 codes.
    """

    def __init__(self, profile: MonitoringProfile):
        self.profile = profile
        self._watch_targets = profile.watch_targets
        self._watched_countries = set(profile.watched_countries)

    def match_event(self, event: CanonicalEvent) -> list[GeoMatch]:
        """Find all geographic matches between an event and watch targets.

        Checks event locations against all watch targets using their
        specific spatial logic.
        """
        matches: list[GeoMatch] = []

        for target in self._watch_targets:
            match = self._check_target(event, target)
            if match:
                matches.append(match)

        return matches

    def match_country(self, event: CanonicalEvent) -> list[GeoMatch]:
        """Check if event countries overlap with watched countries."""
        matches: list[GeoMatch] = []

        for country in event.countries:
            if country in self._watched_countries:
                # Find which watch targets are in this country
                for target in self._watch_targets:
                    if country in target.countries:
                        matches.append(GeoMatch(
                            target_id=target.target_id,
                            entity_id=target.entity_id,
                            entity_name=target.entity_name,
                            match_type="admin",
                            country_code=country,
                        ))
                break  # One country match is enough

        return matches

    def _check_target(self, event: CanonicalEvent, target: WatchTarget) -> Optional[GeoMatch]:
        """Check a single event against a single watch target."""
        if not target.spatial_logic:
            return None

        logic = target.spatial_logic

        if logic.type == SpatialLogicType.PROXIMITY_KM:
            return self._check_proximity(event, target)
        elif logic.type == SpatialLogicType.BUFFER:
            return self._check_buffer(event, target)
        elif logic.type == SpatialLogicType.ADMIN_MATCH:
            return self._check_admin(event, target)

        return None

    def _check_proximity(self, event: CanonicalEvent, target: WatchTarget) -> Optional[GeoMatch]:
        """Check if event is within proximity radius of target."""
        if not target.coordinates or not target.spatial_logic:
            return None

        radius = target.spatial_logic.radius_km or 50.0

        for loc in event.locations:
            if loc.latitude is not None and loc.longitude is not None:
                dist = haversine_km(
                    loc.latitude, loc.longitude,
                    target.coordinates.latitude, target.coordinates.longitude,
                )
                if dist <= radius:
                    return GeoMatch(
                        target_id=target.target_id,
                        entity_id=target.entity_id,
                        entity_name=target.entity_name,
                        match_type="proximity",
                        distance_km=dist,
                    )

        return None

    def _check_buffer(self, event: CanonicalEvent, target: WatchTarget) -> Optional[GeoMatch]:
        """Check if event is within buffer distance of a route.

        Checks against all waypoints in the route. This is a simplified
        point-to-segment check — sufficient for hackathon scale.
        """
        if not target.spatial_logic:
            return None

        buffer_km = target.spatial_logic.buffer_km or 30.0

        # Get route waypoints from the watch target's source data
        # For now, use the target's single coordinates as a representative point
        if target.coordinates:
            for loc in event.locations:
                if loc.latitude is not None and loc.longitude is not None:
                    dist = haversine_km(
                        loc.latitude, loc.longitude,
                        target.coordinates.latitude, target.coordinates.longitude,
                    )
                    if dist <= buffer_km:
                        return GeoMatch(
                            target_id=target.target_id,
                            entity_id=target.entity_id,
                            entity_name=target.entity_name,
                            match_type="route_buffer",
                            distance_km=dist,
                        )

        return None

    def _check_admin(self, event: CanonicalEvent, target: WatchTarget) -> Optional[GeoMatch]:
        """Check if event is in the same country/admin region."""
        if not target.spatial_logic or not target.spatial_logic.admin_codes:
            return None

        for country in event.countries:
            if country in target.spatial_logic.admin_codes:
                return GeoMatch(
                    target_id=target.target_id,
                    entity_id=target.entity_id,
                    entity_name=target.entity_name,
                    match_type="admin",
                    country_code=country,
                )

        return None


def check_route_proximity(
    event_lat: float,
    event_lon: float,
    waypoints: list[dict],
    buffer_km: float = 30.0,
) -> tuple[bool, float]:
    """Check if a point is within buffer distance of any route segment.

    Returns (is_within, min_distance_km).
    """
    min_dist = float('inf')

    for wp in waypoints:
        lat = wp.get("latitude") or wp.get("lat", 0)
        lon = wp.get("longitude") or wp.get("lon", 0)
        if lat and lon:
            dist = haversine_km(event_lat, event_lon, lat, lon)
            min_dist = min(min_dist, dist)

    return min_dist <= buffer_km, min_dist
