"""
Alert manager.

Alert lifecycle: creation, deduplication, cooldown, suppression.
Alerts are attached to situation_ids. New evidence about the same
situation updates existing alerts. 100 reports → 1 alert.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import uuid4

from loguru import logger

from ..models.situations import Alert, RelevanceBreakdown, Situation
from ..models.state import AlertSeverity


class AlertManager:
    """Manages alert lifecycle with fatigue prevention.

    Core invariant: one situation → one active alert (with updates).
    """

    def __init__(
        self,
        cooldown_minutes: int = 30,
        max_per_situation_per_hour: int = 2,
    ):
        self.cooldown = timedelta(minutes=cooldown_minutes)
        self.max_per_hour = max_per_situation_per_hour
        self._alerts: dict[str, Alert] = {}  # alert_id → Alert
        self._situation_alerts: dict[str, list[str]] = {}  # situation_id → [alert_ids]
        self._alert_timestamps: dict[str, list[datetime]] = {}  # situation_id → [timestamps]

    def create_or_update_alert(
        self,
        situation: Situation,
        severity: AlertSeverity,
        evidence_path: list[str] | None = None,
        why_it_matters: list[str] | None = None,
    ) -> Optional[Alert]:
        """Create a new alert or update existing for this situation.

        Returns the alert if created/updated, None if suppressed.
        """
        # Check cooldown
        if self._is_in_cooldown(situation.situation_id):
            logger.debug(f"Alert suppressed for {situation.situation_id} — cooldown active")
            return None

        # Check rate limit
        if self._exceeds_rate_limit(situation.situation_id):
            logger.debug(f"Alert suppressed for {situation.situation_id} — rate limit")
            return None

        # Check for existing alert to update
        existing = self._find_active_alert(situation.situation_id)
        if existing:
            return self._update_alert(existing, situation, severity, why_it_matters)

        # Create new alert
        alert = self._create_alert(situation, severity, evidence_path, why_it_matters)
        self._register_alert(alert)

        logger.info(
            f"ALERT_CREATED: {alert.alert_id} severity={severity.value} "
            f"situation={situation.situation_id}"
        )
        return alert

    def get_alert(self, alert_id: str) -> Optional[Alert]:
        return self._alerts.get(alert_id)

    def get_alerts(
        self,
        severity: Optional[AlertSeverity] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Alert]:
        """Get alerts with optional filtering."""
        alerts = sorted(
            self._alerts.values(),
            key=lambda a: a.created_at,
            reverse=True,
        )
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        return alerts[offset:offset + limit]

    def latest_alert(self) -> Optional[Alert]:
        """Get the most recent alert."""
        if not self._alerts:
            return None
        return max(self._alerts.values(), key=lambda a: a.created_at)

    def all_alerts(self) -> list[Alert]:
        return list(self._alerts.values())

    def _create_alert(
        self,
        situation: Situation,
        severity: AlertSeverity,
        evidence_path: list[str] | None,
        why_it_matters: list[str] | None,
    ) -> Alert:
        alert_id = f"ALT-{uuid4().hex[:8].upper()}"
        idempotency_key = f"{situation.situation_id}_{alert_id}"

        affected_entities = []
        for eid in situation.affected_entity_ids:
            affected_entities.append({"entity_id": eid})

        return Alert(
            alert_id=alert_id,
            network_id=situation.network_id,
            situation_id=situation.situation_id,
            severity=severity,
            event_type=situation.primary_signal_type,
            title=situation.title,
            description=situation.description,
            affected_entities=affected_entities,
            affected_locations=situation.affected_locations,
            affected_routes=situation.affected_routes,
            affected_commodities=situation.affected_commodities,
            relevance=situation.relevance,
            confidence=situation.confidence,
            evidence_path=evidence_path or situation.evidence_path,
            why_it_matters=why_it_matters or situation.why_it_matters,
            idempotency_key=idempotency_key,
        )

    def _update_alert(
        self,
        alert: Alert,
        situation: Situation,
        severity: AlertSeverity,
        why_it_matters: list[str] | None,
    ) -> Alert:
        """Update an existing alert with new information."""
        # Escalate severity if warranted
        severity_order = [AlertSeverity.INFO, AlertSeverity.WATCH,
                          AlertSeverity.WARNING, AlertSeverity.CRITICAL]
        if severity_order.index(severity) > severity_order.index(alert.severity):
            alert.severity = severity

        alert.confidence = max(alert.confidence, situation.confidence)

        if why_it_matters:
            alert.why_it_matters = why_it_matters

        if situation.relevance:
            alert.relevance = situation.relevance

        logger.info(f"ALERT_UPDATED: {alert.alert_id} severity={alert.severity.value}")
        return alert

    def _register_alert(self, alert: Alert) -> None:
        self._alerts[alert.alert_id] = alert

        if alert.situation_id not in self._situation_alerts:
            self._situation_alerts[alert.situation_id] = []
        self._situation_alerts[alert.situation_id].append(alert.alert_id)

        if alert.situation_id not in self._alert_timestamps:
            self._alert_timestamps[alert.situation_id] = []
        self._alert_timestamps[alert.situation_id].append(alert.created_at)

    def _find_active_alert(self, situation_id: str) -> Optional[Alert]:
        """Find the most recent active alert for a situation."""
        alert_ids = self._situation_alerts.get(situation_id, [])
        if not alert_ids:
            return None
        # Return most recent
        return self._alerts.get(alert_ids[-1])

    def _is_in_cooldown(self, situation_id: str) -> bool:
        """Check if situation is in cooldown period."""
        timestamps = self._alert_timestamps.get(situation_id, [])
        if not timestamps:
            return False
        last = timestamps[-1]
        return datetime.now(timezone.utc) - last < self.cooldown

    def _exceeds_rate_limit(self, situation_id: str) -> bool:
        """Check if we've exceeded alerts per hour for this situation."""
        timestamps = self._alert_timestamps.get(situation_id, [])
        if not timestamps:
            return False
        one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        recent = [t for t in timestamps if t > one_hour_ago]
        return len(recent) >= self.max_per_hour
