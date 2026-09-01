"""
Adaptive entity monitoring state machine.

Per-entity state: NORMAL → WATCH → ELEVATED → CRITICAL → RECOVERY.
Controls monitoring frequency for that entity's watch targets only.
Global state unaffected by individual entity transitions.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from loguru import logger

from ..models.state import AlertSeverity, EntityState, MonitoringState


class AdaptiveStateManager:
    """Manages per-entity monitoring state transitions.

    Each network entity has independent state. When an entity transitions
    to a higher state, only that entity's watch targets increase frequency.
    """

    def __init__(self):
        self._states: dict[str, EntityState] = {}

    def get_state(self, entity_id: str) -> Optional[EntityState]:
        """Get current state for an entity."""
        return self._states.get(entity_id)

    def initialize_entity(self, entity_id: str, entity_name: str) -> EntityState:
        """Initialize state tracking for an entity."""
        if entity_id not in self._states:
            self._states[entity_id] = EntityState(
                entity_id=entity_id,
                entity_name=entity_name,
            )
        return self._states[entity_id]

    def all_states(self) -> dict[str, EntityState]:
        """Return all entity states."""
        return dict(self._states)

    def escalate(
        self,
        entity_id: str,
        severity: AlertSeverity,
        situation_id: str,
        reason: str,
    ) -> Optional[MonitoringState]:
        """Escalate entity state based on alert severity.

        Returns the new state if changed, None if no change.
        """
        state = self._states.get(entity_id)
        if not state:
            return None

        target_state = self._severity_to_state(severity, state.state)
        if target_state is None:
            return None

        changed = state.transition(target_state, reason)
        if changed:
            state.situation_id = situation_id
            state.last_event_at = datetime.now(timezone.utc)
            logger.info(
                f"STATE_TRANSITION: {state.entity_name} "
                f"{state.previous_state.value} → {state.state.value} "
                f"(reason: {reason})"
            )
            return state.state

        return None

    def try_recovery(self, entity_id: str, reason: str = "No active situations") -> bool:
        """Try to transition an entity toward RECOVERY/NORMAL.

        Called when a situation is resolved. Only de-escalates one step.
        """
        state = self._states.get(entity_id)
        if not state:
            return False

        recovery_path = {
            MonitoringState.CRITICAL: MonitoringState.ELEVATED,
            MonitoringState.ELEVATED: MonitoringState.WATCH,
            MonitoringState.WATCH: MonitoringState.RECOVERY,
            MonitoringState.RECOVERY: MonitoringState.NORMAL,
        }

        target = recovery_path.get(state.state)
        if target:
            changed = state.transition(target, reason)
            if changed:
                logger.info(
                    f"STATE_RECOVERY: {state.entity_name} "
                    f"{state.previous_state.value} → {state.state.value}"
                )
            return changed
        return False

    def _severity_to_state(
        self, severity: AlertSeverity, current: MonitoringState
    ) -> Optional[MonitoringState]:
        """Map alert severity to target monitoring state.

        Only escalates — never de-escalates from a severity-based trigger.
        """
        severity_map = {
            AlertSeverity.CRITICAL: MonitoringState.CRITICAL,
            AlertSeverity.WARNING: MonitoringState.ELEVATED,
            AlertSeverity.WATCH: MonitoringState.WATCH,
            AlertSeverity.INFO: None,
        }

        target = severity_map.get(severity)
        if target is None:
            return None

        # Only escalate, not de-escalate
        state_order = [
            MonitoringState.NORMAL,
            MonitoringState.RECOVERY,
            MonitoringState.WATCH,
            MonitoringState.ELEVATED,
            MonitoringState.CRITICAL,
        ]
        current_idx = state_order.index(current) if current in state_order else 0
        target_idx = state_order.index(target) if target in state_order else 0

        if target_idx > current_idx:
            return target
        return None

    def get_elevated_entities(self) -> list[EntityState]:
        """Return all entities above NORMAL state."""
        return [
            s for s in self._states.values()
            if s.state not in (MonitoringState.NORMAL, MonitoringState.RECOVERY)
        ]

    def get_network_condition(self) -> str:
        """Aggregate network condition from entity states."""
        states = list(self._states.values())
        if not states:
            return "healthy"

        if any(s.state == MonitoringState.CRITICAL for s in states):
            return "critical"
        if any(s.state == MonitoringState.ELEVATED for s in states):
            return "warning"
        if any(s.state == MonitoringState.WATCH for s in states):
            return "watching"
        return "healthy"
