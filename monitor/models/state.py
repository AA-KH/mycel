"""
Monitoring state models.

Two independent state machines:
1. Entity monitoring state — per network node (NORMAL → WATCH → ELEVATED → CRITICAL → RECOVERY)
2. Source health state — per connector (HEALTHY → DEGRADED → DOWN → RECOVERING)

These are never mixed. Supplier A = CRITICAL does not mean GDELT = CRITICAL.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class MonitoringState(str, Enum):
    """Per-entity monitoring state. Controls monitoring intensity."""

    NORMAL = "normal"
    WATCH = "watch"
    ELEVATED = "elevated"
    CRITICAL = "critical"
    RECOVERY = "recovery"


class SourceHealthState(str, Enum):
    """Per-source health state. Independent from entity state."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"
    RECOVERING = "recovering"


class AlertSeverity(str, Enum):
    """Alert severity levels."""

    INFO = "info"
    WATCH = "watch"
    WARNING = "warning"
    CRITICAL = "critical"


class NetworkCondition(str, Enum):
    """Overall network condition (aggregate of entity states)."""

    HEALTHY = "healthy"
    WATCHING = "watching"
    WARNING = "warning"
    CRITICAL = "critical"


# Monitoring frequency multipliers by state.
# Normal = 1.0x, Watch = 2x frequency, Elevated = 4x, Critical = 8x.
STATE_FREQUENCY_MULTIPLIER: dict[MonitoringState, float] = {
    MonitoringState.NORMAL: 1.0,
    MonitoringState.WATCH: 2.0,
    MonitoringState.ELEVATED: 4.0,
    MonitoringState.CRITICAL: 8.0,
    MonitoringState.RECOVERY: 1.5,
}


class EntityState(BaseModel):
    """Tracked monitoring state for a single network entity."""

    entity_id: str
    entity_name: str
    state: MonitoringState = MonitoringState.NORMAL
    previous_state: Optional[MonitoringState] = None
    state_changed_at: Optional[datetime] = None
    reason: Optional[str] = None
    situation_id: Optional[str] = None  # Active situation causing this state
    escalation_count: int = 0
    last_event_at: Optional[datetime] = None

    def transition(self, new_state: MonitoringState, reason: str) -> bool:
        """Transition to a new state. Returns True if state actually changed."""
        if new_state == self.state:
            return False
        self.previous_state = self.state
        self.state = new_state
        self.state_changed_at = datetime.now(timezone.utc)
        self.reason = reason
        if new_state.value > (self.previous_state.value if self.previous_state else ""):
            self.escalation_count += 1
        return True


class SourceHealth(BaseModel):
    """Tracked health for a single source connector."""

    source_name: str
    state: SourceHealthState = SourceHealthState.HEALTHY
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None
    last_error: Optional[str] = None
    consecutive_failures: int = 0
    total_requests: int = 0
    total_failures: int = 0
    last_response_time_ms: Optional[float] = None

    def record_success(self, response_time_ms: float | None = None) -> None:
        """Record a successful fetch."""
        self.last_success = datetime.now(timezone.utc)
        self.consecutive_failures = 0
        self.total_requests += 1
        self.last_response_time_ms = response_time_ms
        if self.state in (SourceHealthState.DOWN, SourceHealthState.DEGRADED):
            self.state = SourceHealthState.RECOVERING
        elif self.state == SourceHealthState.RECOVERING:
            self.state = SourceHealthState.HEALTHY

    def record_failure(self, error: str) -> None:
        """Record a failed fetch."""
        self.last_failure = datetime.now(timezone.utc)
        self.last_error = error
        self.consecutive_failures += 1
        self.total_requests += 1
        self.total_failures += 1
        if self.consecutive_failures >= 5:
            self.state = SourceHealthState.DOWN
        elif self.consecutive_failures >= 2:
            self.state = SourceHealthState.DEGRADED
