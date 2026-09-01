"""
GDELT DOC 2.0 API connector.

Primary broad news/event intelligence source. Uses profile-derived targeted
queries rather than indiscriminately ingesting everything. Respects rate
limits (≥6s between requests). Handles intermittent availability gracefully.

Signal types: SUPPLIER_DISRUPTION, PORT_DISRUPTION, GEOPOLITICAL,
              REGULATORY, TRADE_POLICY, LABOR_ACTION, FINANCIAL_DISTRESS
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
from ..models.events import CanonicalEvent, EventLocation
from ..models.signals import SignalType
from .base import SourceConnector


class GDELTConnector(SourceConnector):
    """GDELT DOC 2.0 API connector.

    Verified API: https://api.gdeltproject.org/api/v2/doc/doc
    No authentication required.
    Rate limit: ≥6 seconds between requests.
    """

    def __init__(self, config: MonitorConfig):
        super().__init__(
            name="gdelt",
            signal_types=[
                SignalType.SUPPLIER_DISRUPTION,
                SignalType.PORT_DISRUPTION,
                SignalType.GEOPOLITICAL,
                SignalType.REGULATORY,
                SignalType.TRADE_POLICY,
                SignalType.LABOR_ACTION,
                SignalType.FINANCIAL_DISTRESS,
                SignalType.INFRASTRUCTURE_DAMAGE,
            ],
        )
        self.config = config
        self.base_url = config.gdelt_base_url
        self.min_interval = config.gdelt_min_request_interval
        self.max_records = config.gdelt_max_records
        self.timeout = config.gdelt_timeout
        self._last_request_time: float = 0
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def _throttle(self) -> None:
        """Enforce minimum interval between requests."""
        elapsed = time.monotonic() - self._last_request_time
        if elapsed < self.min_interval:
            await asyncio.sleep(self.min_interval - elapsed)
        self._last_request_time = time.monotonic()

    async def fetch(self, query: str | None = None, **kwargs: Any) -> list[CanonicalEvent]:
        """Fetch articles from GDELT matching the query.

        Uses ArtList mode for structured article data.
        """
        if not query:
            return []

        await self._throttle()

        params = {
            "query": query,
            "mode": "ArtList",
            "maxrecords": str(self.max_records),
            "format": "json",
            "sort": "DateDesc",
            "timespan": kwargs.get("timespan", "24h"),
        }

        start = time.monotonic()
        try:
            client = await self._get_client()
            response = await client.get(self.base_url, params=params)
            response_time = (time.monotonic() - start) * 1000

            if response.status_code == 429:
                logger.warning("GDELT rate limited (429). Backing off.")
                self.record_failure("rate_limited")
                await asyncio.sleep(self.min_interval * 3)
                return []

            response.raise_for_status()
            self.record_success(response_time)

            data = response.json()
            return self._normalize(data, query)

        except httpx.TimeoutException:
            logger.warning(f"GDELT request timed out for query: {query[:80]}...")
            self.record_failure("timeout")
            return []
        except httpx.HTTPError as e:
            logger.warning(f"GDELT HTTP error: {e}")
            self.record_failure(str(e))
            return []
        except Exception as e:
            logger.error(f"GDELT unexpected error: {e}")
            self.record_failure(str(e))
            return []

    def _normalize(self, data: dict, query: str) -> list[CanonicalEvent]:
        """Normalize GDELT response into CanonicalEvents."""
        events: list[CanonicalEvent] = []

        articles = data.get("articles", [])
        if not articles:
            return events

        for article in articles:
            try:
                url = article.get("url", "")
                title = article.get("title", "")
                if not title:
                    continue

                # Extract date
                date_str = article.get("seendate", "")
                event_time = None
                if date_str:
                    try:
                        event_time = datetime.strptime(
                            date_str[:14], "%Y%m%d%H%M%S"
                        ).replace(tzinfo=timezone.utc)
                    except (ValueError, IndexError):
                        pass

                # Content hash for deduplication
                content = f"{title}|{url}"
                content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
                title_hash = hashlib.sha256(title.lower().encode()).hexdigest()[:16]

                # Extract location info from GDELT metadata
                locations: list[EventLocation] = []
                source_country = article.get("sourcecountry", "")

                # Determine signal type from context
                signal_type = self._classify_signal(title, article)

                event = CanonicalEvent(
                    event_id=f"gdelt_{uuid4().hex[:12]}",
                    source="gdelt",
                    source_event_id=url,
                    source_url=url,
                    event_time=event_time,
                    signal_type=signal_type,
                    title=title,
                    description=article.get("title", ""),
                    locations=locations,
                    countries=[source_country] if source_country else [],
                    content_hash=content_hash,
                    title_hash=title_hash,
                    confidence=0.5,
                    source_trust=0.6,  # Established news aggregator
                    source_metadata={
                        "domain": article.get("domain", ""),
                        "language": article.get("language", ""),
                        "source_country": source_country,
                        "tone": article.get("tone", ""),
                        "query": query,
                    },
                )
                event.log(f"Ingested from GDELT (query: {query[:50]})")
                events.append(event)

            except Exception as e:
                logger.debug(f"GDELT: Failed to normalize article: {e}")
                continue

        return events

    def _classify_signal(self, title: str, article: dict) -> SignalType:
        """Classify an article into a signal type based on content."""
        title_lower = title.lower()

        disruption_words = {"shutdown", "closure", "fire", "explosion", "bankrupt",
                           "insolvent", "halt", "suspended", "collapse"}
        port_words = {"port", "harbor", "shipping", "dock", "vessel", "cargo"}
        trade_words = {"tariff", "sanction", "export ban", "import restriction", "trade"}
        geo_words = {"conflict", "political", "coup", "unrest", "military", "war"}
        labor_words = {"strike", "walkout", "protest", "union", "labor dispute"}
        financial_words = {"bankruptcy", "debt", "default", "insolvency", "liquidation"}
        regulatory_words = {"regulation", "compliance", "law", "policy change"}

        if any(w in title_lower for w in labor_words):
            return SignalType.LABOR_ACTION
        if any(w in title_lower for w in financial_words):
            return SignalType.FINANCIAL_DISTRESS
        if any(w in title_lower for w in port_words):
            return SignalType.PORT_DISRUPTION
        if any(w in title_lower for w in trade_words):
            return SignalType.TRADE_POLICY
        if any(w in title_lower for w in geo_words):
            return SignalType.GEOPOLITICAL
        if any(w in title_lower for w in regulatory_words):
            return SignalType.REGULATORY
        if any(w in title_lower for w in disruption_words):
            return SignalType.SUPPLIER_DISRUPTION

        return SignalType.SUPPLIER_DISRUPTION  # Default for entity-matched articles

    async def health_check(self) -> bool:
        """Quick health check — try a minimal query."""
        try:
            client = await self._get_client()
            await self._throttle()
            response = await client.get(
                self.base_url,
                params={"query": "test", "mode": "ArtList", "maxrecords": "1", "format": "json"},
            )
            return response.status_code == 200
        except Exception:
            return False

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
