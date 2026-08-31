"""
Open-Meteo weather forecast API connector.

Network-specific weather monitoring. Batches up to 1000 coordinates per
request. No API key needed. Monitors precipitation, wind speed, temperature
extremes at network-relevant locations only.

Free tier: 10,000 calls/day, 5,000/hour, 600/minute.

Signal types: WEATHER_HAZARD
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

# Thresholds for severe weather (configurable)
SEVERE_THRESHOLDS = {
    "precipitation_mm": 50.0,  # Heavy rainfall
    "wind_speed_kmh": 80.0,  # Strong wind
    "temperature_max_c": 45.0,  # Extreme heat
    "temperature_min_c": -20.0,  # Extreme cold
}


class OpenMeteoConnector(SourceConnector):
    """Open-Meteo weather forecast connector.

    Fetches weather forecasts for network-relevant locations. Uses batch
    requests to minimize API calls.
    """

    def __init__(self, config: MonitorConfig):
        super().__init__(
            name="openmeteo",
            signal_types=[SignalType.WEATHER_HAZARD],
        )
        self.config = config
        self.base_url = config.openmeteo_base_url
        self.batch_size = config.openmeteo_batch_size
        self.timeout = config.openmeteo_timeout
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def fetch(self, query: str | None = None, **kwargs: Any) -> list[CanonicalEvent]:
        """Fetch weather forecasts for given coordinates.

        Args:
            coordinates: List of (lat, lon, name, node_id) tuples
        """
        coordinates = kwargs.get("coordinates", [])
        if not coordinates:
            return []

        all_events: list[CanonicalEvent] = []

        # Batch coordinates
        for i in range(0, len(coordinates), self.batch_size):
            batch = coordinates[i:i + self.batch_size]
            events = await self._fetch_batch(batch)
            all_events.extend(events)

        return all_events

    async def _fetch_batch(self, coordinates: list[dict]) -> list[CanonicalEvent]:
        """Fetch weather for a batch of coordinates."""
        lats = ",".join(str(c["lat"]) for c in coordinates)
        lons = ",".join(str(c["lon"]) for c in coordinates)

        params = {
            "latitude": lats,
            "longitude": lons,
            "daily": "precipitation_sum,wind_speed_10m_max,temperature_2m_max,temperature_2m_min",
            "timezone": "auto",
            "forecast_days": "3",
        }

        start = time.monotonic()
        try:
            client = await self._get_client()
            response = await client.get(self.base_url, params=params)
            response_time = (time.monotonic() - start) * 1000
            response.raise_for_status()
            self.record_success(response_time)

            data = response.json()
            return self._normalize(data, coordinates)

        except httpx.TimeoutException:
            logger.warning("Open-Meteo request timed out")
            self.record_failure("timeout")
            return []
        except httpx.HTTPError as e:
            logger.warning(f"Open-Meteo HTTP error: {e}")
            self.record_failure(str(e))
            return []
        except Exception as e:
            logger.error(f"Open-Meteo unexpected error: {e}")
            self.record_failure(str(e))
            return []

    def _normalize(self, data: dict | list, coordinates: list[dict]) -> list[CanonicalEvent]:
        """Normalize Open-Meteo response into CanonicalEvents for severe weather."""
        events: list[CanonicalEvent] = []

        # Handle both single and batch responses
        if isinstance(data, list):
            results = data
        elif "daily" in data:
            results = [data]
        else:
            return events

        for idx, result in enumerate(results):
            if idx >= len(coordinates):
                break

            coord = coordinates[idx]
            daily = result.get("daily", {})

            precip = daily.get("precipitation_sum", [])
            wind = daily.get("wind_speed_10m_max", [])
            temp_max = daily.get("temperature_2m_max", [])
            temp_min = daily.get("temperature_2m_min", [])
            dates = daily.get("time", [])

            for day_idx in range(len(dates)):
                hazards = []

                p = precip[day_idx] if day_idx < len(precip) and precip[day_idx] is not None else 0
                w = wind[day_idx] if day_idx < len(wind) and wind[day_idx] is not None else 0
                tmax = temp_max[day_idx] if day_idx < len(temp_max) and temp_max[day_idx] is not None else 25
                tmin = temp_min[day_idx] if day_idx < len(temp_min) and temp_min[day_idx] is not None else 10

                if p > SEVERE_THRESHOLDS["precipitation_mm"]:
                    hazards.append(f"Heavy rainfall ({p:.0f}mm)")
                if w > SEVERE_THRESHOLDS["wind_speed_kmh"]:
                    hazards.append(f"Strong wind ({w:.0f}km/h)")
                if tmax > SEVERE_THRESHOLDS["temperature_max_c"]:
                    hazards.append(f"Extreme heat ({tmax:.0f}°C)")
                if tmin < SEVERE_THRESHOLDS["temperature_min_c"]:
                    hazards.append(f"Extreme cold ({tmin:.0f}°C)")

                if not hazards:
                    continue

                # Only create events for genuinely severe conditions
                location_name = coord.get("name", f"({coord['lat']}, {coord['lon']})")
                node_id = coord.get("node_id", "")
                date_str = dates[day_idx] if day_idx < len(dates) else "upcoming"

                title = f"Weather hazard at {location_name}: {', '.join(hazards)}"
                content = f"{title}|{date_str}|{coord['lat']}|{coord['lon']}"
                content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

                # Severity based on how far beyond thresholds
                severity_factor = 0.0
                if p > SEVERE_THRESHOLDS["precipitation_mm"]:
                    severity_factor = max(severity_factor, p / 100)
                if w > SEVERE_THRESHOLDS["wind_speed_kmh"]:
                    severity_factor = max(severity_factor, w / 150)

                confidence = min(0.85, 0.6 + severity_factor * 0.2)
                if day_idx == 0:
                    confidence = min(0.9, confidence + 0.1)  # Today's forecast more reliable

                event = CanonicalEvent(
                    event_id=f"openmeteo_{uuid4().hex[:12]}",
                    source="openmeteo",
                    source_event_id=f"weather_{coord['lat']}_{coord['lon']}_{date_str}",
                    event_time=datetime.now(timezone.utc),
                    signal_type=SignalType.WEATHER_HAZARD,
                    event_type="severe_weather",
                    title=title,
                    description=f"Forecast for {date_str}: {', '.join(hazards)}",
                    locations=[EventLocation(
                        name=location_name,
                        latitude=coord["lat"],
                        longitude=coord["lon"],
                    )],
                    matched_node_ids=[node_id] if node_id else [],
                    content_hash=content_hash,
                    title_hash=hashlib.sha256(title.lower().encode()).hexdigest()[:16],
                    confidence=confidence,
                    source_trust=0.8,  # Weather models are good but not perfect
                    source_metadata={
                        "precipitation_mm": p,
                        "wind_speed_kmh": w,
                        "temperature_max_c": tmax,
                        "temperature_min_c": tmin,
                        "forecast_date": date_str,
                        "forecast_day_index": day_idx,
                        "node_id": node_id,
                        "hazards": hazards,
                    },
                )
                event.log(f"Weather hazard detected at {location_name}: {', '.join(hazards)}")
                events.append(event)

        return events

    async def health_check(self) -> bool:
        """Check if Open-Meteo API is reachable."""
        try:
            client = await self._get_client()
            response = await client.get(
                self.base_url,
                params={"latitude": "0", "longitude": "0", "daily": "precipitation_sum", "forecast_days": "1"},
            )
            return response.status_code == 200
        except Exception:
            return False

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
