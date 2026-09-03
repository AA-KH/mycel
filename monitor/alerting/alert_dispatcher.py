"""
Alert dispatcher.

POSTs alerts to the main Mycel backend webhook. Timeout, retries,
exponential backoff, idempotency keys. Does not block the pipeline.

The wire format is translated into the shape the main backend's
``AlertPayload`` (backend/api/v1/routes/monitor.py) accepts:

    {
        "alert_id": str,
        "severity": "CRITICAL" | "WARNING" | "WATCH" | "INFO",
        "title": str,
        "description": str,
        "affected_entities": [str, ...],
        "project_id": str | None,
        "monitor_alert": { ...full Alert dump... }   # extra context
    }

The main backend ignores unknown fields, so the full alert is attached
under ``monitor_alert`` for downstream consumers that want it.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Optional

import httpx
from loguru import logger

from ..config import MonitorConfig
from ..models.situations import Alert


def build_webhook_payload(alert: Alert, project_id: Optional[str] = None) -> dict[str, Any]:
    """Translate a monitor Alert into the main backend's AlertPayload schema."""
    affected: list[str] = []
    for entity in alert.affected_entities:
        if isinstance(entity, dict):
            value = entity.get("entity_name") or entity.get("entity_id")
        else:
            value = entity
        if value and str(value) not in affected:
            affected.append(str(value))

    # Also surface locations, routes, and commodities so the main backend's
    # architect sees the full constraint set without parsing monitor_alert.
    for value in (
        list(alert.affected_locations)
        + list(alert.affected_routes)
        + list(alert.affected_commodities)
    ):
        if value and str(value) not in affected:
            affected.append(str(value))

    description = alert.description or alert.title
    if alert.why_it_matters:
        description = f"{description}\n\nWhy it matters:\n- " + "\n- ".join(alert.why_it_matters)

    return {
        "alert_id": alert.alert_id,
        "severity": alert.severity.value.upper(),
        "title": alert.title,
        "description": description,
        "affected_entities": affected,
        "project_id": project_id or None,
        "monitor_alert": alert.model_dump(mode="json"),
    }


class AlertDispatcher:
    """Dispatches alerts to the main Mycel organization via webhook."""

    def __init__(self, config: MonitorConfig):
        self.webhook_url = config.alert_webhook_url
        self.timeout = config.alert_webhook_timeout
        self.max_retries = config.alert_webhook_max_retries
        self.project_id: Optional[str] = config.alert_project_id
        self._client: httpx.AsyncClient | None = None

    @property
    def is_configured(self) -> bool:
        return bool(self.webhook_url)

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def dispatch(self, alert: Alert, project_id: Optional[str] = None) -> bool:
        """Dispatch an alert to the webhook. Returns True on success.

        Retries with exponential backoff. Uses idempotency key to
        prevent duplicate processing on the receiving end.
        """
        if not self.is_configured:
            logger.warning(
                f"Alert {alert.alert_id} NOT dispatched — set "
                f"MYCEL_MONITOR_ALERT_WEBHOOK_URL to the main backend webhook"
            )
            alert.dispatched = False
            return False

        payload = build_webhook_payload(alert, project_id or self.project_id)
        last_error: Optional[str] = None

        for attempt in range(self.max_retries + 1):
            try:
                client = await self._get_client()
                headers = {
                    "Content-Type": "application/json",
                    "X-Idempotency-Key": alert.idempotency_key or alert.alert_id,
                    "X-Alert-Severity": alert.severity.value,
                }

                logger.info(
                    f"ALERT_DISPATCHING: {alert.alert_id} severity={alert.severity.value} "
                    f"→ {self.webhook_url} (attempt {attempt + 1}/{self.max_retries + 1})"
                )
                response = await client.post(
                    self.webhook_url,
                    json=payload,
                    headers=headers,
                )
                alert.dispatch_attempts += 1

                if response.status_code in (200, 201, 202, 204):
                    alert.dispatched = True
                    alert.dispatched_at = datetime.now(timezone.utc)
                    logger.info(f"ALERT_DISPATCHED: {alert.alert_id} → {self.webhook_url}")
                    return True

                # Surface the backend's error body — a 422 here means the
                # payload shape does not match the main backend's schema.
                body = response.text[:500]
                last_error = f"HTTP {response.status_code}: {body}"
                logger.warning(f"Alert dispatch failed: {last_error}")

                # 4xx (other than 408/429) will not succeed on retry.
                if 400 <= response.status_code < 500 and response.status_code not in (408, 429):
                    break

            except httpx.TimeoutException:
                last_error = "timeout"
                logger.warning(f"Alert dispatch timeout (attempt {attempt + 1})")
                alert.dispatch_attempts += 1
            except httpx.HTTPError as e:
                last_error = str(e)
                logger.warning(f"Alert dispatch HTTP error: {e} (attempt {attempt + 1})")
                alert.dispatch_attempts += 1
            except Exception as e:
                last_error = str(e)
                logger.error(f"Alert dispatch unexpected error: {e}")
                alert.dispatch_attempts += 1
                break  # Don't retry on unexpected errors

            # Exponential backoff
            if attempt < self.max_retries:
                await asyncio.sleep(2 ** attempt)

        logger.error(
            f"ALERT_DISPATCH_FAILED: {alert.alert_id} after {alert.dispatch_attempts} "
            f"attempt(s) — last error: {last_error}"
        )
        return False

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
