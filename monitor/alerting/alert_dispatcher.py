"""
Alert dispatcher.

POSTs alerts to configured webhook. Timeout, retries, exponential
backoff, idempotency keys. Does not block the pipeline.
"""

from __future__ import annotations

import asyncio
from typing import Optional

import httpx
from loguru import logger

from ..config import MonitorConfig
from ..models.situations import Alert


class AlertDispatcher:
    """Dispatches alerts to the main Mycel organization via webhook."""

    def __init__(self, config: MonitorConfig):
        self.webhook_url = config.alert_webhook_url
        self.timeout = config.alert_webhook_timeout
        self.max_retries = config.alert_webhook_max_retries
        self._client: httpx.AsyncClient | None = None

    @property
    def is_configured(self) -> bool:
        return bool(self.webhook_url)

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def dispatch(self, alert: Alert) -> bool:
        """Dispatch an alert to the webhook. Returns True on success.

        Retries with exponential backoff. Uses idempotency key to
        prevent duplicate processing on the receiving end.
        """
        if not self.is_configured:
            logger.debug(f"Alert {alert.alert_id} — no webhook configured, skipping dispatch")
            alert.dispatched = False
            return False

        payload = alert.model_dump(mode="json")

        for attempt in range(self.max_retries + 1):
            try:
                client = await self._get_client()
                headers = {
                    "Content-Type": "application/json",
                    "X-Idempotency-Key": alert.idempotency_key or alert.alert_id,
                    "X-Alert-Severity": alert.severity.value,
                }

                response = await client.post(
                    self.webhook_url,
                    json=payload,
                    headers=headers,
                )
                alert.dispatch_attempts += 1

                if response.status_code in (200, 201, 202, 204):
                    alert.dispatched = True
                    from datetime import datetime, timezone
                    alert.dispatched_at = datetime.now(timezone.utc)
                    logger.info(f"ALERT_DISPATCHED: {alert.alert_id} → {self.webhook_url}")
                    return True

                logger.warning(
                    f"Alert dispatch failed: {response.status_code} "
                    f"(attempt {attempt + 1}/{self.max_retries + 1})"
                )

            except httpx.TimeoutException:
                logger.warning(f"Alert dispatch timeout (attempt {attempt + 1})")
                alert.dispatch_attempts += 1
            except httpx.HTTPError as e:
                logger.warning(f"Alert dispatch HTTP error: {e} (attempt {attempt + 1})")
                alert.dispatch_attempts += 1
            except Exception as e:
                logger.error(f"Alert dispatch unexpected error: {e}")
                alert.dispatch_attempts += 1
                break  # Don't retry on unexpected errors

            # Exponential backoff
            if attempt < self.max_retries:
                wait = 2 ** attempt
                await asyncio.sleep(wait)

        logger.error(f"ALERT_DISPATCH_FAILED: {alert.alert_id} after {self.max_retries + 1} attempts")
        return False

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
