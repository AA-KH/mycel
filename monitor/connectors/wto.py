"""
WTO Timeseries API connector.

Periodic state observer — NOT an event firehose. Polls WTO tariff/trade
indicators, compares against previously observed values, and emits a
CanonicalEvent only when a value changes.

First observation → baseline stored, no event emitted.
Same value → no event, events_unchanged incremented.
Changed value → CanonicalEvent with old + new values.

Requires API key from https://apiportal.wto.org (free registration).
Auth: Ocp-Apim-Subscription-Key header.
Rate limit: 1 request/second.

Signal types: TRADE_POLICY, TRADE_RESTRICTION
"""

from __future__ import annotations

import asyncio
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


# WTO indicator codes → signal type mapping
INDICATOR_SIGNALS: dict[str, SignalType] = {
    "HS_A_0010": SignalType.TRADE_POLICY,       # Applied tariff, simple average
    "HS_B_0010": SignalType.TRADE_POLICY,       # Bound tariff, simple average
    "HS_P_0010": SignalType.TRADE_POLICY,       # Preferential tariff
}

# Default indicators to query
DEFAULT_INDICATORS = ["HS_A_0010"]


class WTOConnector(SourceConnector):
    """WTO Timeseries API — diff-based state observer.

    Queries tariff indicators for watched trade lanes (reporter/partner/HS code).
    Stores last-observed values. Emits events only when values change.
    """

    def __init__(self, config: MonitorConfig):
        super().__init__(
            name="wto",
            signal_types=[SignalType.TRADE_POLICY, SignalType.TRADE_RESTRICTION],
        )
        self.config = config
        self.base_url = config.wto_base_url
        self.api_key = config.wto_api_key
        self.timeout = config.wto_timeout
        self.min_interval = config.wto_min_request_interval
        self._client: httpx.AsyncClient | None = None
        self._last_request_time: float = 0.0

        # State storage: key = (reporter, partner, hs_code, indicator) → last value
        self._last_observed: dict[str, dict] = {}

    @property
    def is_configured(self) -> bool:
        """WTO requires an API key."""
        return bool(self.api_key)

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def _rate_limit(self) -> None:
        """Enforce 1 request/second rate limit."""
        elapsed = time.monotonic() - self._last_request_time
        if elapsed < self.min_interval:
            await asyncio.sleep(self.min_interval - elapsed)
        self._last_request_time = time.monotonic()

    async def fetch(self, query: str | None = None, **kwargs: Any) -> list[CanonicalEvent]:
        """Fetch tariff data and emit events for changed values.

        Accepts query_group kwargs:
            countries: list[str] — ISO3 codes (first=reporter, rest=partners)
            hs_codes: list[str] — HS product codes
            indicators: list[str] — WTO indicator codes (default: applied tariff)
        """
        if not self.is_configured:
            return []

        countries = kwargs.get("countries", [])
        hs_codes = kwargs.get("hs_codes", [])
        indicators = kwargs.get("indicators", DEFAULT_INDICATORS)

        if not countries:
            return []

        events: list[CanonicalEvent] = []
        reporter = countries[0]
        partners = countries[1:] if len(countries) > 1 else ["000"]  # 000 = World

        for partner in partners:
            for hs_code in (hs_codes or [""]):
                for indicator in indicators:
                    new_events = await self._fetch_indicator(
                        reporter=reporter,
                        partner=partner,
                        hs_code=hs_code,
                        indicator=indicator,
                    )
                    events.extend(new_events)

        return events

    async def _fetch_indicator(
        self,
        reporter: str,
        partner: str,
        hs_code: str,
        indicator: str,
    ) -> list[CanonicalEvent]:
        """Fetch a single indicator and diff against last observation."""
        await self._rate_limit()

        params: dict[str, str] = {
            "i": indicator,
            "r": reporter,
            "p": partner,
            "fmt": "json",
            "ps": "last",  # Latest available period
        }
        if hs_code:
            params["pc"] = hs_code

        start = time.monotonic()
        try:
            client = await self._get_client()
            headers = {"Ocp-Apim-Subscription-Key": self.api_key or ""}

            response = await client.get(
                f"{self.base_url}/data",
                params=params,
                headers=headers,
            )
            response_time = (time.monotonic() - start) * 1000

            if response.status_code == 401:
                logger.warning("WTO API: invalid API key")
                self.record_failure("auth_error")
                return []

            if response.status_code == 429:
                logger.warning("WTO API: rate limit exceeded")
                self.record_failure("rate_limit")
                return []

            response.raise_for_status()
            self.record_success(response_time)

            data = response.json()
            return self._diff_and_normalize(data, reporter, partner, hs_code, indicator)

        except httpx.TimeoutException:
            logger.warning("WTO API request timed out")
            self.record_failure("timeout")
            return []
        except httpx.HTTPError as e:
            logger.warning(f"WTO HTTP error: {e}")
            self.record_failure(str(e))
            return []
        except Exception as e:
            logger.error(f"WTO unexpected error: {e}")
            self.record_failure(str(e))
            return []

    def _diff_and_normalize(
        self,
        data: dict,
        reporter: str,
        partner: str,
        hs_code: str,
        indicator: str,
    ) -> list[CanonicalEvent]:
        """Compare fetched data against last observation, emit events on change."""
        events: list[CanonicalEvent] = []
        dataset = data.get("Dataset", [])

        if not dataset:
            return []

        for record in dataset:
            value = record.get("Value")
            period = record.get("Period", "")
            product_code = record.get("ProductCode", hs_code)
            product_name = record.get("ProductDescription", "")

            if value is None:
                continue

            # Build observation key
            obs_key = f"{reporter}|{partner}|{product_code}|{indicator}|{period}"

            # Check against last observation
            previous = self._last_observed.get(obs_key)

            # Store current observation
            current_obs = {
                "value": value,
                "period": period,
                "product_code": product_code,
                "product_name": product_name,
                "reporter": reporter,
                "partner": partner,
                "indicator": indicator,
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            }
            self._last_observed[obs_key] = current_obs

            if previous is None:
                # First observation — store baseline, no event
                continue

            if previous["value"] == value:
                # No change — skip
                continue

            # VALUE CHANGED — emit CanonicalEvent
            old_value = previous["value"]
            signal_type = INDICATOR_SIGNALS.get(indicator, SignalType.TRADE_POLICY)

            commodity_label = product_name or f"HS {product_code}" if product_code else "general"
            title = f"Tariff change: {commodity_label} {old_value}% → {value}% ({reporter} → {partner})"

            content_hash = hashlib.sha256(
                f"wto|{obs_key}|{old_value}|{value}".encode()
            ).hexdigest()[:16]

            commodities = []
            if product_name:
                commodities.append(product_name.lower())

            countries = [reporter]
            if partner and partner != "000":
                countries.append(partner)

            event = CanonicalEvent(
                event_id=f"wto_{uuid4().hex[:12]}",
                source="wto",
                source_event_id=obs_key,
                event_time=datetime.now(timezone.utc),
                signal_type=signal_type,
                event_type="tariff_change",
                title=title,
                description=(
                    f"WTO data shows tariff for {commodity_label} changed from "
                    f"{old_value}% to {value}% on trade lane {reporter} → {partner} "
                    f"(indicator: {indicator}, period: {period})"
                ),
                countries=countries,
                commodities=commodities,
                content_hash=content_hash,
                title_hash=hashlib.sha256(title.lower().encode()).hexdigest()[:16],
                confidence=0.95,
                source_trust=0.95,  # Official WTO data
                source_metadata={
                    "indicator": indicator,
                    "old_value": old_value,
                    "new_value": value,
                    "tariff_period": period,
                    "hs_code": product_code,
                    "product_name": product_name,
                    "reporter": reporter,
                    "partner": partner,
                },
            )
            event.log(f"WTO tariff change detected: {old_value}% → {value}%")
            events.append(event)

        return events

    async def health_check(self) -> bool:
        """Check if WTO API is reachable."""
        if not self.is_configured:
            return False
        try:
            client = await self._get_client()
            headers = {"Ocp-Apim-Subscription-Key": self.api_key or ""}
            response = await client.get(
                f"{self.base_url}/indicators",
                headers=headers,
                params={"fmt": "json", "lang": 1},
            )
            return response.status_code == 200
        except Exception:
            return False

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
