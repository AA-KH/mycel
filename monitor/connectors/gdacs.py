"""
GDACS GeoJSON API connector.

Structured disaster intelligence: earthquakes, cyclones, floods, droughts,
wildfires, volcanoes. No authentication required. Returns machine-readable
geographic and severity information.

Verified live: https://www.gdacs.org/gdacsapi/api/events/geteventlist/SEARCH

Signal types: NATURAL_DISASTER
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

# GDACS event type codes
GDACS_EVENT_TYPES = {
    "EQ": "earthquake",
    "TC": "tropical_cyclone",
    "FL": "flood",
    "DR": "drought",
    "WF": "wildfire",
    "VO": "volcano",
}

# GDACS alert level to trust score
GDACS_ALERT_TRUST = {
    "Red": 0.95,
    "Orange": 0.85,
    "Green": 0.7,
}


class GDACSConnector(SourceConnector):
    """GDACS disaster alert connector.

    Uses the structured GeoJSON API. No authentication needed.
    Returns events with coordinates, severity, affected countries.
    """

    def __init__(self, config: MonitorConfig):
        super().__init__(
            name="gdacs",
            signal_types=[SignalType.NATURAL_DISASTER],
        )
        self.config = config
        self.base_url = f"{config.gdacs_base_url}/events/geteventlist/SEARCH"
        self.timeout = config.gdacs_timeout
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def fetch(self, query: str | None = None, **kwargs: Any) -> list[CanonicalEvent]:
        """Fetch disaster events from GDACS.

        Supports filtering by alert level, event type, and time range.
        """
        params: dict[str, str] = {
            "alertlevel": kwargs.get("alertlevel", "Green;Orange;Red"),
            "eventtype": kwargs.get("eventtype", "EQ,TC,FL,DR,WF,VO"),
        }
        if "limit" in kwargs:
            params["limit"] = str(kwargs["limit"])

        start = time.monotonic()
        try:
            client = await self._get_client()
            response = await client.get(self.base_url, params=params)
            response_time = (time.monotonic() - start) * 1000
            response.raise_for_status()
            self.record_success(response_time)

            data = response.json()
            return self._normalize(data)

        except httpx.TimeoutException:
            logger.warning("GDACS request timed out")
            self.record_failure("timeout")
            return []
        except httpx.HTTPError as e:
            logger.warning(f"GDACS HTTP error: {e}")
            self.record_failure(str(e))
            return []
        except Exception as e:
            logger.error(f"GDACS unexpected error: {e}")
            self.record_failure(str(e))
            return []

    def _normalize(self, data: dict) -> list[CanonicalEvent]:
        """Normalize GDACS GeoJSON into CanonicalEvents."""
        events: list[CanonicalEvent] = []
        features = data.get("features", [])

        for feature in features:
            try:
                props = feature.get("properties", {})
                geometry = feature.get("geometry", {})
                coords = geometry.get("coordinates", [None, None])

                event_type_code = props.get("eventtype", "")
                event_type = GDACS_EVENT_TYPES.get(event_type_code, event_type_code)
                event_id_num = props.get("eventid", "")
                episode_id = props.get("episodeid", "")

                # Build stable source ID for deduplication
                source_event_id = f"gdacs_{event_type_code}_{event_id_num}_{episode_id}"

                title = props.get("name", props.get("description", "Unknown disaster"))
                description = props.get("htmldescription", "")

                # Parse dates
                event_time = None
                from_date = props.get("fromdate", "")
                if from_date:
                    try:
                        event_time = datetime.fromisoformat(from_date.replace("Z", "+00:00"))
                    except ValueError:
                        pass

                # Location
                locations: list[EventLocation] = []
                country_name = props.get("country", "")
                if coords and len(coords) >= 2 and coords[0] is not None:
                    locations.append(EventLocation(
                        latitude=coords[1] if len(coords) > 1 else coords[0],
                        longitude=coords[0],
                        country_name=country_name,
                    ))

                # Affected countries (ISO3)
                affected = props.get("affectedcountries", [])
                countries = [c.get("iso3", "") for c in affected if c.get("iso3")]
                iso3 = props.get("iso3", "")
                if iso3 and iso3 not in countries:
                    countries.append(iso3)

                # Severity from GDACS structured data
                severity_data = props.get("severitydata", {})
                severity_value = severity_data.get("severity", 0)
                severity_text = severity_data.get("severitytext", "")

                # Alert level → trust/confidence
                alert_level = props.get("alertlevel", "Green")
                alert_score = props.get("alertscore", 1)
                trust = GDACS_ALERT_TRUST.get(alert_level, 0.7)

                # Confidence based on alert level and whether current
                is_current = props.get("iscurrent", "true") == "true"
                confidence = trust * (0.9 if is_current else 0.6)

                content_hash = hashlib.sha256(source_event_id.encode()).hexdigest()[:16]

                event = CanonicalEvent(
                    event_id=f"gdacs_{uuid4().hex[:12]}",
                    source="gdacs",
                    source_event_id=source_event_id,
                    source_url=props.get("url", {}).get("report", ""),
                    event_time=event_time,
                    signal_type=SignalType.NATURAL_DISASTER,
                    event_type=event_type,
                    title=title,
                    description=description,
                    locations=locations,
                    countries=countries,
                    content_hash=content_hash,
                    title_hash=hashlib.sha256(title.lower().encode()).hexdigest()[:16],
                    confidence=confidence,
                    source_trust=0.9,  # Official disaster coordination system
                    source_metadata={
                        "gdacs_event_type": event_type_code,
                        "gdacs_event_id": str(event_id_num),
                        "gdacs_episode_id": str(episode_id),
                        "alert_level": alert_level,
                        "alert_score": alert_score,
                        "severity_value": severity_value,
                        "severity_text": severity_text,
                        "is_current": is_current,
                        "source_origin": props.get("source", ""),
                    },
                )
                event.log(f"Ingested from GDACS ({alert_level} {event_type})")
                events.append(event)

            except Exception as e:
                logger.debug(f"GDACS: Failed to normalize feature: {e}")
                continue

        return events

    async def health_check(self) -> bool:
        """Check if GDACS API is reachable."""
        try:
            client = await self._get_client()
            response = await client.get(
                self.base_url,
                params={"alertlevel": "Red", "eventtype": "EQ", "limit": "1"},
            )
            return response.status_code == 200
        except Exception:
            return False

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
