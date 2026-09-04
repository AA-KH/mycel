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


# ISO2 → ISO3 for the trade partners most likely to appear in tariff feeds.
# The network architecture uses ISO3 codes, so incoming ISO2 codes must be
# normalized or the relevance gate will reject the event.
_ISO2_TO_ISO3: dict[str, str] = {
    "US": "USA", "IN": "IND", "CN": "CHN", "DE": "DEU", "JP": "JPN", "KR": "KOR",
    "VN": "VNM", "MX": "MEX", "CA": "CAN", "GB": "GBR", "FR": "FRA", "IT": "ITA",
    "ES": "ESP", "NL": "NLD", "BE": "BEL", "PL": "POL", "TR": "TUR", "BR": "BRA",
    "AR": "ARG", "AU": "AUS", "NZ": "NZL", "SG": "SGP", "MY": "MYS", "TH": "THA",
    "ID": "IDN", "PH": "PHL", "BD": "BGD", "PK": "PAK", "LK": "LKA", "AE": "ARE",
    "SA": "SAU", "EG": "EGY", "ZA": "ZAF", "NG": "NGA", "KE": "KEN", "TW": "TWN",
    "HK": "HKG", "CH": "CHE", "SE": "SWE", "NO": "NOR", "DK": "DNK", "FI": "FIN",
    "IE": "IRL", "PT": "PRT", "AT": "AUT", "CZ": "CZE", "HU": "HUN", "RO": "ROU",
    "GR": "GRC", "IL": "ISR", "RU": "RUS", "UA": "UKR", "CL": "CHL", "CO": "COL",
    "PE": "PER", "EU": "EUR",
}

# Country names → ISO3 so a CMD payload can use names in place of codes.
_NAME_TO_ISO3: dict[str, str] = {
    "united states": "USA", "usa": "USA", "u.s.": "USA", "america": "USA",
    "india": "IND", "china": "CHN", "germany": "DEU", "japan": "JPN",
    "south korea": "KOR", "korea": "KOR", "vietnam": "VNM", "mexico": "MEX",
    "canada": "CAN", "united kingdom": "GBR", "uk": "GBR", "france": "FRA",
    "italy": "ITA", "spain": "ESP", "netherlands": "NLD", "brazil": "BRA",
    "australia": "AUS", "singapore": "SGP", "malaysia": "MYS", "thailand": "THA",
    "indonesia": "IDN", "bangladesh": "BGD", "pakistan": "PAK", "taiwan": "TWN",
    "european union": "EUR", "eu": "EUR", "turkey": "TUR", "russia": "RUS",
}


def normalize_country_code(value: Any) -> str | None:
    """Return an ISO3 code for an ISO2 code, ISO3 code, or country name."""
    if not value:
        return None
    raw = str(value).strip()
    if not raw:
        return None
    upper = raw.upper()
    if len(upper) == 3 and upper.isalpha():
        return upper
    if len(upper) == 2 and upper in _ISO2_TO_ISO3:
        return _ISO2_TO_ISO3[upper]
    return _NAME_TO_ISO3.get(raw.lower(), upper)


def _to_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


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

    def _normalize(self, data: dict | list, *, skip_seen: bool = True) -> list[CanonicalEvent]:
        """Normalize TradeWatch tariff data into CanonicalEvents.

        ``skip_seen`` controls the connector-level dedup set. Polling passes
        True (default) so repeated feed reads don't re-emit. The push webhook
        passes False so the pipeline's own deduplicator decides, and a
        re-sent CMD payload is not silently swallowed here.
        """
        events: list[CanonicalEvent] = []

        if isinstance(data, list):
            items = data
        elif isinstance(data, dict) and "imposingCountry" in data:
            # A single tariff object (the demo / CMD payload shape)
            items = [data]
        elif isinstance(data, dict):
            items = data.get("data") or data.get("items") or data.get("alerts") or []
        else:
            items = []

        for item in items:
            if not isinstance(item, dict):
                continue
            try:
                imposing_code = normalize_country_code(
                    item.get("imposingCountry") or item.get("imposingCountryName")
                )
                target_code = normalize_country_code(
                    item.get("targetCountry") or item.get("targetCountryName")
                )

                event_hash = (
                    f"{imposing_code or ''}-{target_code or ''}-"
                    f"{item.get('sector', '')}-{item.get('newRatePercent', '')}"
                )

                if skip_seen and event_hash in self._seen_events:
                    logger.debug(f"TradeWatch: skipping already-seen tariff {event_hash}")
                    continue
                self._seen_events.add(event_hash)

                imposing_country = item.get("imposingCountryName") or imposing_code or "Unknown"
                target_country = item.get("targetCountryName") or target_code or "Unknown"
                sector = str(item.get("sector") or "unknown")
                old_rate = _to_float(item.get("previousRatePercent"))
                new_rate = _to_float(item.get("newRatePercent"))
                delta = _to_float(item.get("delta"))
                if delta is None and old_rate is not None and new_rate is not None:
                    delta = new_rate - old_rate
                date = item.get("effectiveDate", "")
                basis = item.get("legalBasis", "")
                notes = item.get("notes", "")

                old_str = f"{old_rate:g}" if old_rate is not None else "unknown"
                new_str = f"{new_rate:g}" if new_rate is not None else "unknown"
                delta_str = f"{delta:g}" if delta is not None else "unknown"

                title = f"URGENT: Tariff Increase by {imposing_country} on {target_country} ({sector})"
                description = (
                    f"A new tariff has been imposed by {imposing_country} on {target_country} "
                    f"for sector {sector}. The rate has increased from {old_str}% to {new_str}% "
                    f"(a {delta_str}% increase). Effective Date: {date}. Legal Basis: {basis}."
                )
                if notes:
                    description += f" Notes: {notes}"

                content_hash = hashlib.sha256(event_hash.encode()).hexdigest()[:16]

                # Keep the raw item, but add the keys the relevance engine's
                # severity classifier reads (old_value/new_value/intervention_type).
                metadata: dict[str, Any] = dict(item)
                metadata.setdefault("intervention_type", "tariff_increase")
                if old_rate is not None:
                    metadata.setdefault("old_value", old_rate)
                if new_rate is not None:
                    metadata.setdefault("new_value", new_rate)
                metadata["imposing_country_iso3"] = imposing_code
                metadata["target_country_iso3"] = target_code

                countries = [c for c in (target_code, imposing_code) if c]
                raw_entities = [
                    e for e in (
                        item.get("targetCountryName"),
                        item.get("imposingCountryName"),
                        sector,
                    ) if e
                ]

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
                    countries=countries,
                    commodities=[sector.lower()],
                    raw_entities=raw_entities,
                    content_hash=content_hash,
                    title_hash=hashlib.sha256(title.lower().encode()).hexdigest()[:16],
                    confidence=0.95,  # Direct API data
                    source_trust=0.9,
                    source_metadata=metadata,
                )
                event.log(f"TradeWatch tariff: {imposing_country} -> {target_country} ({sector})")
                events.append(event)

            except Exception as e:
                logger.warning(f"TradeWatch: Failed to normalize item: {e}")
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
