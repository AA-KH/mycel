"""
changedetection.io connector (Tier 2 — Optional).

Targeted supplier/website monitoring. Requires a running changedetection.io
instance. Dynamically registers and manages watches for supplier URLs from
the monitoring profile.

Only activated when CHANGEDETECTION_URL and CHANGEDETECTION_API_KEY are configured.

Signal types: SUPPLIER_DISRUPTION
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


class ChangeDetectionConnector(SourceConnector):
    """changedetection.io REST API connector.

    Manages watches for supplier URLs derived from the monitoring profile.
    Polls for detected changes or receives webhook notifications.
    """

    def __init__(self, config: MonitorConfig):
        super().__init__(
            name="changedetection",
            signal_types=[SignalType.SUPPLIER_DISRUPTION],
        )
        self.config = config
        self.base_url = config.changedetection_url
        self.api_key = config.changedetection_api_key
        self.timeout = config.changedetection_timeout
        self._client: httpx.AsyncClient | None = None
        self._managed_watches: dict[str, str] = {}  # url → watch_uuid

    @property
    def is_configured(self) -> bool:
        """Check if changedetection.io is configured."""
        return bool(self.base_url and self.api_key)

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            headers = {"x-api-key": self.api_key or ""}
            self._client = httpx.AsyncClient(timeout=self.timeout, headers=headers)
        return self._client

    async def fetch(self, query: str | None = None, **kwargs: Any) -> list[CanonicalEvent]:
        """Fetch recent changes from managed watches."""
        if not self.is_configured:
            return []

        start = time.monotonic()
        try:
            client = await self._get_client()
            response = await client.get(f"{self.base_url}/api/v1/watch")
            response_time = (time.monotonic() - start) * 1000
            response.raise_for_status()
            self.record_success(response_time)

            watches = response.json()
            return await self._check_for_changes(watches)

        except Exception as e:
            logger.warning(f"ChangeDetection error: {e}")
            self.record_failure(str(e))
            return []

    async def _check_for_changes(self, watches: dict) -> list[CanonicalEvent]:
        """Check which watched URLs have recent changes."""
        events: list[CanonicalEvent] = []

        for watch_uuid, watch_data in watches.items():
            last_changed = watch_data.get("last_changed", 0)
            if last_changed == 0:
                continue

            # Only process recent changes (within last polling interval)
            url = watch_data.get("url", "")
            title = watch_data.get("title", url)

            content_hash = hashlib.sha256(
                f"{url}|{last_changed}".encode()
            ).hexdigest()[:16]

            event = CanonicalEvent(
                event_id=f"cdio_{uuid4().hex[:12]}",
                source="changedetection",
                source_event_id=f"cdio_{watch_uuid}_{last_changed}",
                source_url=url,
                event_time=datetime.fromtimestamp(last_changed, tz=timezone.utc),
                signal_type=SignalType.SUPPLIER_DISRUPTION,
                event_type="website_change",
                title=f"Website change detected: {title}",
                description=f"Change detected at {url}",
                content_hash=content_hash,
                title_hash=hashlib.sha256(title.lower().encode()).hexdigest()[:16],
                confidence=0.4,  # Website change doesn't confirm disruption
                source_trust=0.7,  # Direct observation, but meaning unclear
                source_metadata={
                    "watch_uuid": watch_uuid,
                    "url": url,
                    "last_changed": last_changed,
                },
            )
            event.log(f"Website change detected: {url}")
            events.append(event)

        return events

    async def register_watch(self, url: str, tag: str = "mycel") -> str | None:
        """Register a new URL to watch."""
        if not self.is_configured:
            return None

        try:
            client = await self._get_client()
            response = await client.post(
                f"{self.base_url}/api/v1/watch",
                json={"url": url, "tag": tag},
            )
            if response.status_code in (200, 201):
                data = response.json()
                watch_uuid = data.get("uuid", "")
                self._managed_watches[url] = watch_uuid
                logger.info(f"Registered changedetection watch for {url}")
                return watch_uuid
            return None
        except Exception as e:
            logger.warning(f"Failed to register watch for {url}: {e}")
            return None

    async def health_check(self) -> bool:
        if not self.is_configured:
            return False
        try:
            client = await self._get_client()
            response = await client.get(f"{self.base_url}/api/v1/watch")
            return response.status_code == 200
        except Exception:
            return False

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
