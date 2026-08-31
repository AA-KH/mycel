"""
Objective Manager (Phase 16)

Manages the CompanyObjective lifecycle with explicit state machine validation.

Valid transitions:
  DRAFT       → ACTIVE
  ACTIVE      → PLANNING | PAUSED | CANCELLED
  PLANNING    → EXECUTING | BLOCKED | PAUSED | CANCELLED
  EXECUTING   → EVALUATING | BLOCKED | PAUSED | REPLANNING | COMPLETED | FAILED | CANCELLED
  EVALUATING  → EXECUTING | REPLANNING | COMPLETED | FAILED | PAUSED | CANCELLED
  REPLANNING  → PLANNING | BLOCKED | FAILED | PAUSED | CANCELLED
  BLOCKED     → ACTIVE | REPLANNING | PAUSED | CANCELLED | FAILED
  PAUSED      → ACTIVE | CANCELLED
  (terminal)  COMPLETED | FAILED | CANCELLED | EXPIRED — no further transitions

Invalid transitions raise ValueError.
COMPLETED → ACTIVE and CANCELLED → ACTIVE are explicitly forbidden.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from autonomy.models import (
    CompanyObjective, ObjectiveStatus, AutonomyLevel
)
from autonomy.registry import ObjectiveRegistry

logger = logging.getLogger(__name__)

# State machine: valid transitions from each status
_VALID_TRANSITIONS = {
    ObjectiveStatus.DRAFT:      {ObjectiveStatus.ACTIVE, ObjectiveStatus.CANCELLED},
    ObjectiveStatus.ACTIVE:     {ObjectiveStatus.PLANNING, ObjectiveStatus.PAUSED, ObjectiveStatus.CANCELLED},
    ObjectiveStatus.PLANNING:   {ObjectiveStatus.EXECUTING, ObjectiveStatus.BLOCKED, ObjectiveStatus.PAUSED, ObjectiveStatus.CANCELLED},
    ObjectiveStatus.EXECUTING:  {ObjectiveStatus.EVALUATING, ObjectiveStatus.BLOCKED, ObjectiveStatus.PAUSED, ObjectiveStatus.REPLANNING, ObjectiveStatus.COMPLETED, ObjectiveStatus.FAILED, ObjectiveStatus.CANCELLED},
    ObjectiveStatus.EVALUATING: {ObjectiveStatus.EXECUTING, ObjectiveStatus.REPLANNING, ObjectiveStatus.COMPLETED, ObjectiveStatus.FAILED, ObjectiveStatus.PAUSED, ObjectiveStatus.CANCELLED},
    ObjectiveStatus.REPLANNING: {ObjectiveStatus.PLANNING, ObjectiveStatus.BLOCKED, ObjectiveStatus.FAILED, ObjectiveStatus.PAUSED, ObjectiveStatus.CANCELLED},
    ObjectiveStatus.BLOCKED:    {ObjectiveStatus.ACTIVE, ObjectiveStatus.REPLANNING, ObjectiveStatus.PAUSED, ObjectiveStatus.CANCELLED, ObjectiveStatus.FAILED},
    ObjectiveStatus.PAUSED:     {ObjectiveStatus.ACTIVE, ObjectiveStatus.CANCELLED},
    # Terminal states — no valid outgoing transitions
    ObjectiveStatus.COMPLETED:  set(),
    ObjectiveStatus.FAILED:     set(),
    ObjectiveStatus.CANCELLED:  set(),
    ObjectiveStatus.EXPIRED:    set(),
}

_TERMINAL_STATES = {
    ObjectiveStatus.COMPLETED,
    ObjectiveStatus.FAILED,
    ObjectiveStatus.CANCELLED,
    ObjectiveStatus.EXPIRED,
}


class ObjectiveManager:
    """
    Manages objective lifecycle, enforcing state machine transitions.
    """

    def __init__(self, registry: ObjectiveRegistry):
        self.registry = registry

    # ─────────────────────────────────────────────────────────────────────
    # Create
    # ─────────────────────────────────────────────────────────────────────

    def create(self, objective: CompanyObjective) -> CompanyObjective:
        """Store a new objective in DRAFT status."""
        if objective.status != ObjectiveStatus.DRAFT:
            raise ValueError("New objectives must start in DRAFT status.")
        self.registry.store_objective(objective)
        logger.info(f"[ObjectiveManager] Created objective '{objective.objective_id}': {objective.title!r}")
        return objective

    # ─────────────────────────────────────────────────────────────────────
    # Lifecycle transitions
    # ─────────────────────────────────────────────────────────────────────

    def activate(self, objective_id: str) -> CompanyObjective:
        """DRAFT → ACTIVE."""
        return self._transition(objective_id, ObjectiveStatus.ACTIVE)

    def start_planning(self, objective_id: str) -> CompanyObjective:
        """ACTIVE → PLANNING."""
        return self._transition(objective_id, ObjectiveStatus.PLANNING)

    def start_executing(self, objective_id: str) -> CompanyObjective:
        """PLANNING → EXECUTING."""
        return self._transition(objective_id, ObjectiveStatus.EXECUTING)

    def start_evaluating(self, objective_id: str) -> CompanyObjective:
        """EXECUTING → EVALUATING."""
        return self._transition(objective_id, ObjectiveStatus.EVALUATING)

    def start_replanning(self, objective_id: str) -> CompanyObjective:
        """EXECUTING/EVALUATING → REPLANNING."""
        return self._transition(objective_id, ObjectiveStatus.REPLANNING)

    def mark_blocked(self, objective_id: str) -> CompanyObjective:
        return self._transition(objective_id, ObjectiveStatus.BLOCKED)

    def pause(self, objective_id: str) -> CompanyObjective:
        obj = self._transition(objective_id, ObjectiveStatus.PAUSED)
        logger.info(f"[ObjectiveManager] Paused '{objective_id}' — no new tasks will be created.")
        return obj

    def resume(self, objective_id: str) -> CompanyObjective:
        """PAUSED → ACTIVE."""
        return self._transition(objective_id, ObjectiveStatus.ACTIVE)

    def cancel(self, objective_id: str) -> CompanyObjective:
        """
        Cancel the objective. History is preserved; records are NOT deleted.
        """
        obj = self._load(objective_id)
        if obj.status in _TERMINAL_STATES:
            raise ValueError(
                f"Objective '{objective_id}' is already terminal ({obj.status}). Cannot cancel."
            )
        obj.status = ObjectiveStatus.CANCELLED
        obj.updated_at = datetime.now(timezone.utc)
        self.registry.store_objective(obj)
        logger.info(f"[ObjectiveManager] Cancelled '{objective_id}' — history preserved.")
        return obj

    def complete(self, objective_id: str) -> CompanyObjective:
        """
        Mark objective COMPLETED. Only callable after ObjectiveCompletionValidator
        has confirmed all success criteria are met.
        """
        obj = self._transition(objective_id, ObjectiveStatus.COMPLETED)
        obj.completed_at = datetime.now(timezone.utc)
        self.registry.store_objective(obj)
        logger.info(f"[ObjectiveManager] Objective '{objective_id}' COMPLETED.")
        return obj

    def fail(self, objective_id: str) -> CompanyObjective:
        obj = self._load(objective_id)
        allowed = _VALID_TRANSITIONS.get(obj.status, set())
        if ObjectiveStatus.FAILED not in allowed:
            raise ValueError(
                f"Cannot fail objective from status {obj.status}."
            )
        obj.status = ObjectiveStatus.FAILED
        obj.updated_at = datetime.now(timezone.utc)
        self.registry.store_objective(obj)
        return obj

    def attach_plan(self, objective_id: str, plan_id: str) -> CompanyObjective:
        """Register a new plan version on the objective (append-only)."""
        obj = self._load(objective_id)
        if plan_id not in obj.plan_ids:
            obj.plan_ids.append(plan_id)
        obj.current_plan_id = plan_id
        obj.updated_at = datetime.now(timezone.utc)
        self.registry.store_objective(obj)
        return obj

    def increment_iteration(self, objective_id: str) -> CompanyObjective:
        obj = self._load(objective_id)
        obj.iteration_count += 1
        obj.budget_config.current_iterations += 1
        obj.updated_at = datetime.now(timezone.utc)
        self.registry.store_objective(obj)
        return obj

    # ─────────────────────────────────────────────────────────────────────
    # Internal helpers
    # ─────────────────────────────────────────────────────────────────────

    def _load(self, objective_id: str) -> CompanyObjective:
        obj = self.registry.get_objective(objective_id)
        if not obj:
            raise ValueError(f"Objective '{objective_id}' not found.")
        return obj

    def _transition(self, objective_id: str, new_status: ObjectiveStatus) -> CompanyObjective:
        obj = self._load(objective_id)
        allowed = _VALID_TRANSITIONS.get(obj.status, set())
        if new_status not in allowed:
            raise ValueError(
                f"Invalid transition: {obj.status} → {new_status} "
                f"for objective '{objective_id}'."
            )
        old = obj.status
        obj.status = new_status
        obj.updated_at = datetime.now(timezone.utc)
        self.registry.store_objective(obj)
        logger.debug(f"[ObjectiveManager] '{objective_id}': {old} → {new_status}")
        return obj
