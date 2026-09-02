"""
TradeWatch API connector.

Polls the TradeWatch API for real-time tariff changes.
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
from ..models.events import CanonicalEvent
from ..models.signals import SignalType
from .base import SourceConnector


class TradeWatchConnector(SourceConnector):
    """TradeWatch API connector for real-time tariff intelligence."""

    def __init__(self, config: MonitorConfig):
        super().__init__(
            name="tradewatch",
            signal_types=[
                SignalType.TRADE_POLICY,
                SignalType.TRADE_RESTRICTION,
            ],
        )
        self.config = config
        self.api_url = config.tradewatch_api_url
        self.api_key = config.tradewatch_api_key
        self.timeout = config.tradewatch_timeout
        self._client: httpx.AsyncClient | None = None
        self._seen_events: set[str] = set()

    @property
    def is_configured(self) -> bool:
        return bool(self.api_url and self.api_key)

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def fetch(self, query: str | None = None, **kwargs: Any) -> list[CanonicalEvent]:
        """Fetch tariff changes from TradeWatch."""
        if not self.is_configured:
            return []

        countries = kwargs.get("countries", [])
        hs_codes = kwargs.get("hs_codes", [])

        start = time.monotonic()
        try:
            client = await self._get_client()

            params = {}
            if countries:
                params["target_countries"] = ",".join(countries)
            if hs_codes:
                params["sectors"] = ",".join(hs_codes)

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/json",
            }

            response = await client.get(
                self.api_url,
                params=params,
                headers=headers,
            )
            response_time = (time.monotonic() - start) * 1000

            if response.status_code == 401:
                logger.warning("TradeWatch API: authentication failed")
                self.record_failure("auth_error")
                return []

            response.raise_for_status()
            self.record_success(response_time)

            data = response.json()
            return self._normalize(data)

        except Exception as e:
            logger.error(f"TradeWatch unexpected error: {e}")
            self.record_failure(str(e))
            return []

    def _normalize(self, data: dict | list) -> list[CanonicalEvent]:
        """Normalize TradeWatch tariff data into CanonicalEvents."""
        events: list[CanonicalEvent] = []

        items = data if isinstance(data, list) else data.get("data", [])

        # If data is a single object not in a list (like the demo payload)
        if isinstance(data, dict) and "imposingCountry" in data:
            items = [data]

        for item in items:
            try:
                # Generate a unique ID based on the event attributes if an ID isn't provided
                event_hash = f"{item.get('imposingCountry', '')}-{item.get('targetCountry', '')}-{item.get('sector', '')}-{item.get('newRatePercent', '')}"
                
                if event_hash in self._seen_events:
                    continue
                self._seen_events.add(event_hash)

                imposing_country = item.get("imposingCountryName", item.get("imposingCountry", ""))
                target_country = item.get("targetCountryName", item.get("targetCountry", ""))
                sector = item.get("sector", "unknown")
                old_rate = item.get("previousRatePercent", "unknown")
                new_rate = item.get("newRatePercent", "unknown")
                delta = item.get("delta", "unknown")
                date = item.get("effectiveDate", "")
                basis = item.get("legalBasis", "")

                title = f"URGENT: Tariff Increase by {imposing_country} on {target_country} ({sector})"
                description = f"A new tariff has been imposed by {imposing_country} on {target_country} for sector {sector}. The rate has increased from {old_rate}% to {new_rate}% (a {delta}% increase). Effective Date: {date}. Legal Basis: {basis}."
                
                content_hash = hashlib.sha256(event_hash.encode()).hexdigest()[:16]

                event = CanonicalEvent(
                    event_id=f"tw_{uuid4().hex[:12]}",
                    source="tradewatch",
                    source_event_id=event_hash,
                    source_url="",
                    event_time=datetime.now(timezone.utc),
                    signal_type=SignalType.TRADE_POLICY,
                    event_type="tariff_increase",
                    title=title,
                    description=description,
                    countries=[item.get("targetCountry", ""), item.get("imposingCountry", "")],
                    commodities=[sector.lower()],
                    content_hash=content_hash,
                    title_hash=hashlib.sha256(title.lower().encode()).hexdigest()[:16],
                    confidence=0.95, # Direct API data
                    source_trust=0.9,
                    source_metadata=item,
                )
                event.log(f"TradeWatch tariff: {imposing_country} -> {target_country}")
                events.append(event)

            except Exception as e:
                logger.debug(f"TradeWatch: Failed to normalize item: {e}")
                continue

        return events

    async def health_check(self) -> bool:
        if not self.is_configured:
            return False
        try:
            client = await self._get_client()
            response = await client.get(
                self.api_url,
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            return response.status_code == 200
        except Exception:
            return False

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
