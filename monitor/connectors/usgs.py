"""
USGS Earthquake GeoJSON feed connector.

Fast earthquake-specific source. Uses summary feeds for polling and FDSN
query API for targeted geographic searches. Filters by magnitude and
geography BEFORE any downstream processing.

Verified live: https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_hour.geojson

Signal types: EARTHQUAKE
"""

from __future__ import annotations

import hashlib
import time
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import httpx
from loguru import logger

from ..config import MonitorConfig
from ..models.events import CanonicalEvent, EventLocation
from ..models.signals import SignalType
from .base import SourceConnector


class USGSConnector(SourceConnector):
    """USGS earthquake data connector.

    Two modes:
    1. Summary feed polling (4.5+ magnitude, hourly/daily)
    2. FDSN query API for targeted geographic searches
    """

    def __init__(self, config: MonitorConfig):
        super().__init__(
            name="usgs",
            signal_types=[SignalType.EARTHQUAKE],
        )
        self.config = config
        self.feed_url = config.usgs_feed_url
        self.query_url = config.usgs_query_url
        self.min_magnitude = config.usgs_min_magnitude
        self.timeout = config.usgs_timeout
        self._client: httpx.AsyncClient | None = None
        self._last_etag: str | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def fetch(self, query: str | None = None, **kwargs: Any) -> list[CanonicalEvent]:
        """Fetch earthquake data.

        Default: polls the 4.5+ magnitude hourly summary feed.
        With geographic params: uses FDSN query API for targeted search.
        """
        if kwargs.get("latitude") and kwargs.get("longitude"):
            return await self._fetch_targeted(**kwargs)
        return await self._fetch_summary(**kwargs)

    async def _fetch_summary(self, **kwargs: Any) -> list[CanonicalEvent]:
        """Fetch from the pre-generated summary feed."""
        feed = kwargs.get("feed", "4.5_hour")
        url = f"{self.feed_url}/{feed}.geojson"

        start = time.monotonic()
        try:
            client = await self._get_client()

            # Conditional request with ETag
            headers = {}
            if self._last_etag:
                headers["If-None-Match"] = self._last_etag

            response = await client.get(url, headers=headers)
            response_time = (time.monotonic() - start) * 1000

            if response.status_code == 304:
                # Not modified — no new data
                self.record_success(response_time)
                return []

            response.raise_for_status()
            self.record_success(response_time)

            # Cache ETag for next request
            self._last_etag = response.headers.get("ETag")

            data = response.json()
            return self._normalize(data)

        except httpx.TimeoutException:
            logger.warning("USGS feed request timed out")
            self.record_failure("timeout")
            return []
        except httpx.HTTPError as e:
            logger.warning(f"USGS HTTP error: {e}")
            self.record_failure(str(e))
            return []
        except Exception as e:
            logger.error(f"USGS unexpected error: {e}")
            self.record_failure(str(e))
            return []

    async def _fetch_targeted(self, **kwargs: Any) -> list[CanonicalEvent]:
        """Fetch earthquakes near specific coordinates using FDSN API."""
        params = {
            "format": "geojson",
            "latitude": str(kwargs["latitude"]),
            "longitude": str(kwargs["longitude"]),
            "maxradiuskm": str(kwargs.get("radius_km", 200)),
            "minmagnitude": str(kwargs.get("min_magnitude", self.min_magnitude)),
            "limit": str(kwargs.get("limit", 20)),
            "orderby": "time",
        }

        start = time.monotonic()
        try:
            client = await self._get_client()
            response = await client.get(self.query_url, params=params)
            response_time = (time.monotonic() - start) * 1000
            response.raise_for_status()
            self.record_success(response_time)

            data = response.json()
            return self._normalize(data)

        except Exception as e:
            logger.warning(f"USGS targeted query error: {e}")
            self.record_failure(str(e))
            return []

    def _normalize(self, data: dict) -> list[CanonicalEvent]:
        """Normalize USGS GeoJSON into CanonicalEvents."""
        events: list[CanonicalEvent] = []
        features = data.get("features", [])

        for feature in features:
            try:
                props = feature.get("properties", {})
                geometry = feature.get("geometry", {})
                coords = geometry.get("coordinates", [])

                magnitude = props.get("mag", 0)
                if magnitude is None or magnitude < self.min_magnitude:
                    continue

                place = props.get("place", "Unknown location")
                eq_id = feature.get("id", "")

                # Timestamp (milliseconds since epoch)
                time_ms = props.get("time")
                event_time = None
                if time_ms:
                    event_time = datetime.fromtimestamp(time_ms / 1000, tz=timezone.utc)

                # Location
                locations: list[EventLocation] = []
                if coords and len(coords) >= 2:
                    locations.append(EventLocation(
                        name=place,
                        latitude=coords[1],
                        longitude=coords[0],
                    ))

                # Build title
                title = f"M{magnitude:.1f} Earthquake - {place}"

                # Severity and confidence from USGS data
                sig = props.get("sig", 0)  # Significance 0-1000
                confidence = min(1.0, 0.6 + (sig / 2000)) if sig else 0.7

                content_hash = hashlib.sha256(eq_id.encode()).hexdigest()[:16]

                depth = coords[2] if len(coords) > 2 else None

                event = CanonicalEvent(
                    event_id=f"usgs_{uuid4().hex[:12]}",
                    source="usgs",
                    source_event_id=eq_id,
                    source_url=props.get("url", ""),
                    event_time=event_time,
                    signal_type=SignalType.EARTHQUAKE,
                    event_type="earthquake",
                    title=title,
                    description=f"Magnitude {magnitude:.1f} earthquake at depth {depth:.1f}km" if depth else title,
                    locations=locations,
                    content_hash=content_hash,
                    title_hash=hashlib.sha256(title.lower().encode()).hexdigest()[:16],
                    confidence=confidence,
                    source_trust=0.95,  # Official USGS data
                    source_metadata={
                        "magnitude": magnitude,
                        "magnitude_type": props.get("magType", ""),
                        "depth_km": depth,
                        "significance": sig,
                        "felt": props.get("felt"),
                        "tsunami": props.get("tsunami", 0),
                        "alert": props.get("alert"),  # green/yellow/orange/red
                        "status": props.get("status", ""),
                        "place": place,
                    },
                )
                event.log(f"Ingested from USGS (M{magnitude:.1f})")
                events.append(event)

            except Exception as e:
                logger.debug(f"USGS: Failed to normalize feature: {e}")
                continue

        return events

    async def health_check(self) -> bool:
        """Check if USGS feed is reachable."""
        try:
            client = await self._get_client()
            response = await client.head(f"{self.feed_url}/4.5_hour.geojson")
            return response.status_code == 200
        except Exception:
            return False

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
