"""
Global Trade Alert connector.

Event-like connector — GTA interventions are discrete government actions.
Each intervention has an ID, implementing jurisdiction, affected sectors,
and status. The connector tracks seen intervention IDs to avoid re-emitting.

Requires commercial API license from SGEPT. Without credentials, the
connector reports as unconfigured (like ChangeDetection).

Signal types: TRADE_POLICY, TRADE_RESTRICTION, GEOPOLITICAL, REGULATORY
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


# GTA intervention type → signal type mapping
INTERVENTION_SIGNALS: dict[str, SignalType] = {
    "tariff_increase": SignalType.TRADE_POLICY,
    "tariff_decrease": SignalType.TRADE_POLICY,
    "tariff": SignalType.TRADE_POLICY,
    "antidumping": SignalType.TRADE_POLICY,
    "countervailing": SignalType.TRADE_POLICY,
    "safeguard": SignalType.TRADE_POLICY,
    "export_ban": SignalType.TRADE_RESTRICTION,
    "import_ban": SignalType.TRADE_RESTRICTION,
    "export_restriction": SignalType.TRADE_RESTRICTION,
    "import_restriction": SignalType.TRADE_RESTRICTION,
    "quota": SignalType.TRADE_RESTRICTION,
    "export_quota": SignalType.TRADE_RESTRICTION,
    "import_quota": SignalType.TRADE_RESTRICTION,
    "export_licensing": SignalType.TRADE_RESTRICTION,
    "import_licensing": SignalType.TRADE_RESTRICTION,
    "sanction": SignalType.GEOPOLITICAL,
    "embargo": SignalType.GEOPOLITICAL,
    "subsidy": SignalType.REGULATORY,
    "state_aid": SignalType.REGULATORY,
    "public_procurement": SignalType.REGULATORY,
    "local_content_requirement": SignalType.REGULATORY,
}


class GTAConnector(SourceConnector):
    """Global Trade Alert — government trade-policy intervention intelligence.

    Queries GTA API for interventions filtered by affected countries,
    implementing countries, and affected HS code sectors. Tracks seen
    intervention IDs to avoid re-emitting known policies.
    """

    def __init__(self, config: MonitorConfig):
        super().__init__(
            name="global_trade_alert",
            signal_types=[
                SignalType.TRADE_POLICY,
                SignalType.TRADE_RESTRICTION,
                SignalType.GEOPOLITICAL,
                SignalType.REGULATORY,
            ],
        )
        self.config = config
        self.api_url = config.gta_api_url
        self.api_key = config.gta_api_key
        self.timeout = config.gta_timeout
        self._client: httpx.AsyncClient | None = None

        # Track seen intervention IDs to avoid re-emitting
        self._seen_interventions: set[str] = set()

    @property
    def is_configured(self) -> bool:
        """GTA requires both API URL and API key (commercial license)."""
        return bool(self.api_url and self.api_key)

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def fetch(self, query: str | None = None, **kwargs: Any) -> list[CanonicalEvent]:
        """Fetch trade-policy interventions from GTA.

        Accepts query_group kwargs:
            countries: list[str] — ISO3 codes for affected/implementing jurisdictions
            hs_codes: list[str] — affected HS code sectors
        """
        if not self.is_configured:
            return []

        countries = kwargs.get("countries", [])
        hs_codes = kwargs.get("hs_codes", [])

        start = time.monotonic()
        try:
            client = await self._get_client()

            params: dict[str, Any] = {}
            if countries:
                params["affected_jurisdictions"] = ",".join(countries)
            if hs_codes:
                params["affected_sectors"] = ",".join(hs_codes)
            params["status"] = "in_force,under_review"

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/json",
            }

            response = await client.get(
                f"{self.api_url}/interventions",
                params=params,
                headers=headers,
            )
            response_time = (time.monotonic() - start) * 1000

            if response.status_code == 401:
                logger.warning("GTA API: authentication failed")
                self.record_failure("auth_error")
                return []

            if response.status_code == 403:
                logger.warning("GTA API: access denied (license issue)")
                self.record_failure("access_denied")
                return []

            response.raise_for_status()
            self.record_success(response_time)

            data = response.json()
            return self._normalize(data)

        except httpx.TimeoutException:
            logger.warning("GTA API request timed out")
            self.record_failure("timeout")
            return []
        except httpx.HTTPError as e:
            logger.warning(f"GTA HTTP error: {e}")
            self.record_failure(str(e))
            return []
        except Exception as e:
            logger.error(f"GTA unexpected error: {e}")
            self.record_failure(str(e))
            return []

    def _normalize(self, data: dict | list) -> list[CanonicalEvent]:
        """Normalize GTA intervention data into CanonicalEvents."""
        events: list[CanonicalEvent] = []

        interventions = data if isinstance(data, list) else data.get("interventions", [])

        for intervention in interventions:
            try:
                intervention_id = str(intervention.get("id", intervention.get("intervention_id", "")))
                if not intervention_id:
                    continue

                # Skip already-seen interventions
                if intervention_id in self._seen_interventions:
                    continue
                self._seen_interventions.add(intervention_id)

                # Extract fields
                intervention_type = intervention.get("type", intervention.get("intervention_type", "unknown")).lower()
                implementing = intervention.get("implementing_jurisdiction", intervention.get("implementing", ""))
                affected = intervention.get("affected_jurisdictions", intervention.get("affected", []))
                if isinstance(affected, str):
                    affected = [affected]
                sectors = intervention.get("affected_sectors", intervention.get("sectors", []))
                if isinstance(sectors, str):
                    sectors = [sectors]
                hs_codes = intervention.get("hs_codes", [])
                status = intervention.get("status", "in_force")
                title_raw = intervention.get("title", "")
                description = intervention.get("description", "")
                announcement_date = intervention.get("announcement_date", "")
                implementation_date = intervention.get("implementation_date", "")
                source_url = intervention.get("source_url", intervention.get("url", ""))

                # Determine signal type from intervention type
                signal_type = INTERVENTION_SIGNALS.get(
                    intervention_type, SignalType.TRADE_POLICY
                )

                # Build title
                commodity_label = ", ".join(sectors[:3]) if sectors else "multiple sectors"
                title = title_raw or f"{intervention_type.replace('_', ' ').title()}: {implementing} → {commodity_label} ({status})"

                # Build countries list
                countries: list[str] = []
                if implementing:
                    countries.append(implementing)
                countries.extend(a for a in affected if a not in countries)

                # Build commodities from sectors
                commodities = [s.lower() for s in sectors[:10]]

                content_hash = hashlib.sha256(
                    f"gta|{intervention_id}".encode()
                ).hexdigest()[:16]

                event = CanonicalEvent(
                    event_id=f"gta_{uuid4().hex[:12]}",
                    source="global_trade_alert",
                    source_event_id=intervention_id,
                    source_url=source_url,
                    event_time=datetime.now(timezone.utc),
                    signal_type=signal_type,
                    event_type=intervention_type,
                    title=title,
                    description=description or title,
                    countries=countries,
                    commodities=commodities,
                    content_hash=content_hash,
                    title_hash=hashlib.sha256(title.lower().encode()).hexdigest()[:16],
                    confidence=0.88,
                    source_trust=0.88,  # High-quality curated policy data
                    source_metadata={
                        "intervention_id": intervention_id,
                        "intervention_type": intervention_type,
                        "implementing_jurisdiction": implementing,
                        "affected_jurisdictions": affected,
                        "affected_sectors": sectors,
                        "hs_codes": hs_codes,
                        "announcement_date": announcement_date,
                        "implementation_date": implementation_date,
                        "status": status,
                    },
                )
                event.log(f"GTA intervention: {intervention_type} by {implementing}")
                events.append(event)

            except Exception as e:
                logger.debug(f"GTA: Failed to normalize intervention: {e}")
                continue

        return events

    async def health_check(self) -> bool:
        """Check if GTA API is reachable."""
        if not self.is_configured:
            return False
        try:
            client = await self._get_client()
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/json",
            }
            response = await client.get(
                f"{self.api_url}/status",
                headers=headers,
            )
            return response.status_code == 200
        except Exception:
            return False

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
