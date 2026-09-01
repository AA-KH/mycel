"""
WITS / World Bank connector.

Periodic state observer — NOT an event firehose. Polls the World Bank
WITS SDMX API for tariff and NTM data, compares against previously
observed values, and emits a CanonicalEvent only when a value changes.

This connector surfaces TRAINS-derived tariff and NTM data via the
World Bank WITS infrastructure. It is NOT directly an UNCTAD endpoint.

Public API — no authentication required.

Signal types: TRADE_POLICY, NON_TARIFF_MEASURE, REGULATORY
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


class WITSConnector(SourceConnector):
    """WITS / World Bank — diff-based state observer.

    Queries the WITS SDMX REST API for tariff data (TRAINS-derived)
    and NTM information. Stores last-observed values. Emits events
    only when values change.
    """

    def __init__(self, config: MonitorConfig):
        super().__init__(
            name="wits",
            signal_types=[
                SignalType.TRADE_POLICY,
                SignalType.NON_TARIFF_MEASURE,
                SignalType.REGULATORY,
            ],
        )
        self.config = config
        self.base_url = config.wits_base_url
        self.timeout = config.wits_timeout
        self._client: httpx.AsyncClient | None = None

        # State storage: key = observation_key → last value dict
        self._last_observed: dict[str, dict] = {}

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def fetch(self, query: str | None = None, **kwargs: Any) -> list[CanonicalEvent]:
        """Fetch tariff/NTM data and emit events for changed values.

        Accepts query_group kwargs:
            countries: list[str] — ISO3 codes (first=reporter, rest=partners)
            hs_codes: list[str] — HS product codes
            data_type: str — "tariff" (default) or "ntm"
        """
        countries = kwargs.get("countries", [])
        hs_codes = kwargs.get("hs_codes", [])
        data_type = kwargs.get("data_type", "tariff")

        if not countries:
            return []

        reporter = countries[0]
        partners = countries[1:] if len(countries) > 1 else ["000"]  # 000 = World

        events: list[CanonicalEvent] = []
        for partner in partners:
            for hs_code in (hs_codes or [""]):
                if data_type == "ntm":
                    new_events = await self._fetch_ntm(reporter, hs_code)
                else:
                    new_events = await self._fetch_tariff(reporter, partner, hs_code)
                events.extend(new_events)

        return events

    async def _fetch_tariff(
        self,
        reporter: str,
        partner: str,
        hs_code: str,
    ) -> list[CanonicalEvent]:
        """Fetch tariff data from WITS SDMX API and diff against last observation."""
        # Build SDMX key: reporter.partner.product.reported
        sdmx_key = f"{reporter}.{partner}.{hs_code or 'Total'}.reported"
        url = f"{self.base_url}/DF_WITS_Tariff_TRAINS/{sdmx_key}"

        start = time.monotonic()
        try:
            client = await self._get_client()
            headers = {"Accept": "application/json"}

            response = await client.get(url, headers=headers)
            response_time = (time.monotonic() - start) * 1000

            if response.status_code == 404:
                # No data for this combination — not an error
                return []

            response.raise_for_status()
            self.record_success(response_time)

            data = response.json()
            return self._diff_tariff(data, reporter, partner, hs_code)

        except httpx.TimeoutException:
            logger.warning("WITS API request timed out")
            self.record_failure("timeout")
            return []
        except httpx.HTTPError as e:
            logger.warning(f"WITS HTTP error: {e}")
            self.record_failure(str(e))
            return []
        except Exception as e:
            logger.error(f"WITS unexpected error: {e}")
            self.record_failure(str(e))
            return []

    async def _fetch_ntm(
        self,
        reporter: str,
        hs_code: str,
    ) -> list[CanonicalEvent]:
        """Fetch NTM data from WITS and diff against last observation."""
        url = f"{self.base_url}/DF_WITS_NTM/{reporter}.{hs_code or 'Total'}"

        start = time.monotonic()
        try:
            client = await self._get_client()
            headers = {"Accept": "application/json"}

            response = await client.get(url, headers=headers)
            response_time = (time.monotonic() - start) * 1000

            if response.status_code == 404:
                return []

            response.raise_for_status()
            self.record_success(response_time)

            data = response.json()
            return self._diff_ntm(data, reporter, hs_code)

        except httpx.TimeoutException:
            logger.warning("WITS NTM request timed out")
            self.record_failure("timeout")
            return []
        except httpx.HTTPError as e:
            logger.warning(f"WITS NTM HTTP error: {e}")
            self.record_failure(str(e))
            return []
        except Exception as e:
            logger.error(f"WITS NTM unexpected error: {e}")
            self.record_failure(str(e))
            return []

    def _diff_tariff(
        self,
        data: dict,
        reporter: str,
        partner: str,
        hs_code: str,
    ) -> list[CanonicalEvent]:
        """Diff tariff data against last observation, emit events on change."""
        events: list[CanonicalEvent] = []

        # Navigate SDMX structure to extract observations
        observations = self._extract_sdmx_observations(data)

        for obs in observations:
            value = obs.get("value")
            period = obs.get("period", "")
            product = obs.get("product", hs_code)
            product_name = obs.get("product_name", "")

            if value is None:
                continue

            obs_key = f"wits_tariff|{reporter}|{partner}|{product}|{period}"

            previous = self._last_observed.get(obs_key)
            current_obs = {
                "value": value,
                "period": period,
                "product": product,
                "product_name": product_name,
                "reporter": reporter,
                "partner": partner,
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            }
            self._last_observed[obs_key] = current_obs

            if previous is None:
                continue  # First observation — baseline

            if previous["value"] == value:
                continue  # No change

            # VALUE CHANGED — emit event
            old_value = previous["value"]
            commodity_label = product_name or f"HS {product}" if product else "general"
            title = (
                f"WITS tariff change: {commodity_label} "
                f"{old_value}% → {value}% ({reporter} → {partner})"
            )

            content_hash = hashlib.sha256(
                f"wits_tariff|{obs_key}|{old_value}|{value}".encode()
            ).hexdigest()[:16]

            countries = [reporter]
            if partner and partner != "000":
                countries.append(partner)

            commodities = []
            if product_name:
                commodities.append(product_name.lower())

            event = CanonicalEvent(
                event_id=f"wits_{uuid4().hex[:12]}",
                source="wits",
                source_event_id=obs_key,
                event_time=datetime.now(timezone.utc),
                signal_type=SignalType.TRADE_POLICY,
                event_type="tariff_change",
                title=title,
                description=(
                    f"WITS/TRAINS data shows tariff for {commodity_label} changed from "
                    f"{old_value}% to {value}% on trade lane {reporter} → {partner} "
                    f"(period: {period})"
                ),
                countries=countries,
                commodities=commodities,
                content_hash=content_hash,
                title_hash=hashlib.sha256(title.lower().encode()).hexdigest()[:16],
                confidence=0.92,
                source_trust=0.92,
                source_metadata={
                    "data_source": "wits_trains",
                    "old_value": old_value,
                    "new_value": value,
                    "period": period,
                    "hs_code": product,
                    "product_name": product_name,
                    "reporter": reporter,
                    "partner": partner,
                },
            )
            event.log(f"WITS tariff change: {old_value}% → {value}%")
            events.append(event)

        return events

    def _diff_ntm(
        self,
        data: dict,
        reporter: str,
        hs_code: str,
    ) -> list[CanonicalEvent]:
        """Diff NTM data against last observation, emit events on change."""
        events: list[CanonicalEvent] = []
        observations = self._extract_sdmx_observations(data)

        for obs in observations:
            ntm_type = obs.get("ntm_type", "")
            ntm_count = obs.get("value", 0)
            product = obs.get("product", hs_code)
            product_name = obs.get("product_name", "")

            obs_key = f"wits_ntm|{reporter}|{product}|{ntm_type}"

            previous = self._last_observed.get(obs_key)
            current_obs = {
                "value": ntm_count,
                "ntm_type": ntm_type,
                "product": product,
                "product_name": product_name,
                "reporter": reporter,
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            }
            self._last_observed[obs_key] = current_obs

            if previous is None:
                continue  # First observation

            if previous["value"] == ntm_count:
                continue  # No change

            old_count = previous["value"]
            commodity_label = product_name or f"HS {product}" if product else "general"
            ntm_label = ntm_type.upper() if ntm_type else "NTM"
            title = (
                f"WITS NTM change: {ntm_label} measures on {commodity_label} "
                f"({old_count} → {ntm_count}) in {reporter}"
            )

            content_hash = hashlib.sha256(
                f"wits_ntm|{obs_key}|{old_count}|{ntm_count}".encode()
            ).hexdigest()[:16]

            event = CanonicalEvent(
                event_id=f"wits_{uuid4().hex[:12]}",
                source="wits",
                source_event_id=obs_key,
                event_time=datetime.now(timezone.utc),
                signal_type=SignalType.NON_TARIFF_MEASURE,
                event_type="ntm_change",
                title=title,
                description=(
                    f"WITS/TRAINS data shows {ntm_label} non-tariff measures on "
                    f"{commodity_label} changed from {old_count} to {ntm_count} "
                    f"in {reporter}"
                ),
                countries=[reporter],
                commodities=[product_name.lower()] if product_name else [],
                content_hash=content_hash,
                title_hash=hashlib.sha256(title.lower().encode()).hexdigest()[:16],
                confidence=0.92,
                source_trust=0.92,
                source_metadata={
                    "data_source": "wits_trains",
                    "ntm_type": ntm_type,
                    "old_count": old_count,
                    "new_count": ntm_count,
                    "hs_code": product,
                    "product_name": product_name,
                    "reporter": reporter,
                },
            )
            event.log(f"WITS NTM change: {ntm_label} {old_count} → {ntm_count}")
            events.append(event)

        return events

    def _extract_sdmx_observations(self, data: dict) -> list[dict]:
        """Extract observation records from SDMX JSON response.

        SDMX responses have a deeply nested structure. This method
        extracts the relevant values into flat dicts for diffing.
        """
        observations: list[dict] = []

        try:
            # Try SDMX-JSON structure
            datasets = data.get("dataSets", data.get("DataSets", []))
            if not datasets:
                # Try simpler flat structure
                records = data.get("data", data.get("records", []))
                if isinstance(records, list):
                    return records
                return []

            for dataset in datasets:
                series_data = dataset.get("series", dataset.get("Series", {}))
                for series_key, series in series_data.items():
                    obs_data = series.get("observations", series.get("Observations", {}))
                    attrs = series.get("attributes", [])

                    for time_key, obs_values in obs_data.items():
                        value = obs_values[0] if isinstance(obs_values, list) and obs_values else None
                        observations.append({
                            "value": value,
                            "period": str(time_key),
                            "series_key": series_key,
                        })

        except (KeyError, IndexError, TypeError) as e:
            logger.debug(f"WITS SDMX parsing: {e}")

        return observations

    async def health_check(self) -> bool:
        """Check if WITS API is reachable (public, no auth)."""
        try:
            client = await self._get_client()
            # Use a lightweight metadata request
            response = await client.get(
                f"{self.base_url}/../dataflow",
                headers={"Accept": "application/json"},
            )
            return response.status_code in (200, 301, 302)
        except Exception:
            return False

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
