"""
SQLite persistence.

Minimal, direct SQLite layer. No over-abstracted repository pattern.
Tables: profiles, events, situations, alerts, entity_state,
watch_state, source_health, metrics.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from loguru import logger

from ..models.events import CanonicalEvent
from ..models.situations import Alert, Situation
from ..models.state import EntityState, SourceHealth


SCHEMA = """
CREATE TABLE IF NOT EXISTS profiles (
    profile_id TEXT PRIMARY KEY,
    network_id TEXT NOT NULL,
    architecture_version TEXT,
    compiled_at TEXT NOT NULL,
    profile_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS events (
    event_id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    signal_type TEXT NOT NULL,
    title TEXT NOT NULL,
    detected_at TEXT NOT NULL,
    event_time TEXT,
    content_hash TEXT,
    situation_id TEXT,
    network_id TEXT,
    event_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS situations (
    situation_id TEXT PRIMARY KEY,
    network_id TEXT NOT NULL,
    title TEXT NOT NULL,
    primary_signal_type TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    is_active INTEGER DEFAULT 1,
    event_count INTEGER DEFAULT 0,
    severity TEXT,
    situation_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS alerts (
    alert_id TEXT PRIMARY KEY,
    network_id TEXT NOT NULL,
    situation_id TEXT NOT NULL,
    severity TEXT NOT NULL,
    title TEXT NOT NULL,
    created_at TEXT NOT NULL,
    dispatched INTEGER DEFAULT 0,
    alert_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS entity_state (
    entity_id TEXT PRIMARY KEY,
    entity_name TEXT NOT NULL,
    state TEXT NOT NULL,
    state_changed_at TEXT,
    reason TEXT,
    situation_id TEXT
);

CREATE TABLE IF NOT EXISTS source_health (
    source_name TEXT PRIMARY KEY,
    state TEXT NOT NULL,
    last_success TEXT,
    last_failure TEXT,
    consecutive_failures INTEGER DEFAULT 0,
    total_requests INTEGER DEFAULT 0,
    total_failures INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS metrics (
    metric_name TEXT PRIMARY KEY,
    metric_value INTEGER DEFAULT 0,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_events_source ON events(source);
CREATE INDEX IF NOT EXISTS idx_events_signal ON events(signal_type);
CREATE INDEX IF NOT EXISTS idx_events_situation ON events(situation_id);
CREATE INDEX IF NOT EXISTS idx_alerts_situation ON alerts(situation_id);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity);
CREATE INDEX IF NOT EXISTS idx_situations_active ON situations(is_active);
"""


class MonitorStore:
    """Minimal SQLite persistence for the monitoring subsystem."""

    def __init__(self, db_path: str = "monitor_data.db"):
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None

    def initialize(self) -> None:
        """Create database and tables."""
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(SCHEMA)
        self._conn.commit()
        logger.info(f"Monitor database initialized at {self.db_path}")

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self.initialize()
        return self._conn  # type: ignore

    # ── Profiles ──

    def save_profile(self, profile_id: str, network_id: str, version: str, profile_json: str) -> None:
        conn = self._get_conn()
        conn.execute(
            "INSERT OR REPLACE INTO profiles (profile_id, network_id, architecture_version, compiled_at, profile_json) VALUES (?, ?, ?, ?, ?)",
            (profile_id, network_id, version, datetime.now(timezone.utc).isoformat(), profile_json),
        )
        conn.commit()

    # ── Events ──

    def save_event(self, event: CanonicalEvent, situation_id: Optional[str] = None) -> None:
        conn = self._get_conn()
        conn.execute(
            "INSERT OR REPLACE INTO events (event_id, source, signal_type, title, detected_at, event_time, content_hash, situation_id, network_id, event_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                event.event_id, event.source, event.signal_type.value, event.title,
                event.detected_at.isoformat(),
                event.event_time.isoformat() if event.event_time else None,
                event.content_hash, situation_id, event.network_id,
                event.model_dump_json(),
            ),
        )
        conn.commit()

    def get_recent_events(self, limit: int = 50) -> list[dict]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT event_json FROM events ORDER BY detected_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [json.loads(row["event_json"]) for row in rows]

    # ── Situations ──

    def save_situation(self, situation: Situation) -> None:
        conn = self._get_conn()
        conn.execute(
            "INSERT OR REPLACE INTO situations (situation_id, network_id, title, primary_signal_type, created_at, updated_at, is_active, event_count, severity, situation_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                situation.situation_id, situation.network_id, situation.title,
                situation.primary_signal_type,
                situation.created_at.isoformat(), situation.updated_at.isoformat(),
                1 if situation.is_active else 0, len(situation.event_ids),
                situation.severity.value, situation.model_dump_json(),
            ),
        )
        conn.commit()

    def get_active_situations(self) -> list[dict]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT situation_json FROM situations WHERE is_active = 1 ORDER BY updated_at DESC"
        ).fetchall()
        return [json.loads(row["situation_json"]) for row in rows]

    # ── Alerts ──

    def save_alert(self, alert: Alert) -> None:
        conn = self._get_conn()
        conn.execute(
            "INSERT OR REPLACE INTO alerts (alert_id, network_id, situation_id, severity, title, created_at, dispatched, alert_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                alert.alert_id, alert.network_id, alert.situation_id,
                alert.severity.value, alert.title,
                alert.created_at.isoformat(), 1 if alert.dispatched else 0,
                alert.model_dump_json(),
            ),
        )
        conn.commit()

    def get_alerts(self, severity: Optional[str] = None, limit: int = 50) -> list[dict]:
        conn = self._get_conn()
        if severity:
            rows = conn.execute(
                "SELECT alert_json FROM alerts WHERE severity = ? ORDER BY created_at DESC LIMIT ?",
                (severity, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT alert_json FROM alerts ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [json.loads(row["alert_json"]) for row in rows]

    # ── Entity State ──

    def save_entity_state(self, state: EntityState) -> None:
        conn = self._get_conn()
        conn.execute(
            "INSERT OR REPLACE INTO entity_state (entity_id, entity_name, state, state_changed_at, reason, situation_id) VALUES (?, ?, ?, ?, ?, ?)",
            (
                state.entity_id, state.entity_name, state.state.value,
                state.state_changed_at.isoformat() if state.state_changed_at else None,
                state.reason, state.situation_id,
            ),
        )
        conn.commit()

    # ── Source Health ──

    def save_source_health(self, health: SourceHealth) -> None:
        conn = self._get_conn()
        conn.execute(
            "INSERT OR REPLACE INTO source_health (source_name, state, last_success, last_failure, consecutive_failures, total_requests, total_failures) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                health.source_name, health.state.value,
                health.last_success.isoformat() if health.last_success else None,
                health.last_failure.isoformat() if health.last_failure else None,
                health.consecutive_failures, health.total_requests, health.total_failures,
            ),
        )
        conn.commit()

    # ── Metrics ──

    def update_metric(self, name: str, value: int) -> None:
        conn = self._get_conn()
        conn.execute(
            "INSERT OR REPLACE INTO metrics (metric_name, metric_value, updated_at) VALUES (?, ?, ?)",
            (name, value, datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()

    def get_metrics(self) -> dict[str, int]:
        conn = self._get_conn()
        rows = conn.execute("SELECT metric_name, metric_value FROM metrics").fetchall()
        return {row["metric_name"]: row["metric_value"] for row in rows}

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None
