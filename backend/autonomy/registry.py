"""
Objective Registry (Phase 16)

In-memory store for CompanyObjectives, CompanyPlans, AutonomyDecisions,
AutonomousActions, and AutonomyEscalations.

Interface is designed for MongoDB drop-in replacement.
All plan versions are preserved (no overwrites).
Kill switch state is stored here as single global flag.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

from autonomy.models import (
    CompanyObjective, CompanyPlan, AutonomyDecision,
    AutonomousAction, AutonomyEscalation, AutonomyHealth,
    AutonomyHealthStatus,
)

logger = logging.getLogger(__name__)


class ObjectiveRegistry:
    """
    In-memory registry for all autonomy domain entities.
    Thread-safety: single-process; use async locks in production.
    """

    def __init__(self):
        self._objectives: Dict[str, CompanyObjective] = {}
        self._plans: Dict[str, CompanyPlan] = {}          # plan_id → plan
        self._decisions: Dict[str, List[AutonomyDecision]] = {}  # obj_id → decisions
        self._actions: Dict[str, List[AutonomousAction]] = {}    # obj_id → actions
        self._escalations: Dict[str, List[AutonomyEscalation]] = {}  # obj_id → escalations
        self._kill_switch: bool = False

    # ─────────────────────────────────────────────────────────────────────
    # Objectives
    # ─────────────────────────────────────────────────────────────────────

    def store_objective(self, objective: CompanyObjective) -> None:
        self._objectives[objective.objective_id] = objective
        logger.debug(f"[Registry] Stored objective '{objective.objective_id}'.")

    def get_objective(self, objective_id: str) -> Optional[CompanyObjective]:
        return self._objectives.get(objective_id)

    def list_objectives(self, organization_id: Optional[str] = None) -> List[CompanyObjective]:
        objs = list(self._objectives.values())
        if organization_id:
            objs = [o for o in objs if o.organization_id == organization_id]
        return objs

    def objective_count(self) -> int:
        return len(self._objectives)

    # ─────────────────────────────────────────────────────────────────────
    # Plans — all versions preserved
    # ─────────────────────────────────────────────────────────────────────

    def store_plan(self, plan: CompanyPlan) -> None:
        self._plans[plan.plan_id] = plan
        logger.debug(
            f"[Registry] Stored plan '{plan.plan_id}' "
            f"v{plan.version} for objective '{plan.objective_id}'."
        )

    def get_plan(self, plan_id: str) -> Optional[CompanyPlan]:
        return self._plans.get(plan_id)

    def get_all_plans(self, objective_id: str) -> List[CompanyPlan]:
        """Return all plan versions for an objective, oldest first."""
        plans = [p for p in self._plans.values() if p.objective_id == objective_id]
        return sorted(plans, key=lambda p: p.version)

    # ─────────────────────────────────────────────────────────────────────
    # Decisions (append-only audit log)
    # ─────────────────────────────────────────────────────────────────────

    def record_decision(self, decision: AutonomyDecision) -> None:
        self._decisions.setdefault(decision.objective_id, []).append(decision)

    def get_decisions(self, objective_id: str) -> List[AutonomyDecision]:
        return list(self._decisions.get(objective_id, []))

    def get_last_decision(self, objective_id: str) -> Optional[AutonomyDecision]:
        decisions = self._decisions.get(objective_id, [])
        return decisions[-1] if decisions else None

    # ─────────────────────────────────────────────────────────────────────
    # Actions (append-only audit log)
    # ─────────────────────────────────────────────────────────────────────

    def record_action(self, action: AutonomousAction) -> None:
        self._actions.setdefault(action.objective_id, []).append(action)

    def get_actions(self, objective_id: str) -> List[AutonomousAction]:
        return list(self._actions.get(objective_id, []))

    def get_pending_approvals(self, objective_id: str) -> List[AutonomousAction]:
        from autonomy.models import ActionStatus
        return [
            a for a in self._actions.get(objective_id, [])
            if a.status == ActionStatus.PENDING
        ]

    def update_action_status(self, action_id: str, status, result_reference: Optional[str] = None) -> bool:
        for actions in self._actions.values():
            for a in actions:
                if a.action_id == action_id:
                    a.status = status
                    if result_reference:
                        a.result_reference = result_reference
                    a.completed_at = datetime.now(timezone.utc)
                    return True
        return False

    # ─────────────────────────────────────────────────────────────────────
    # Escalations
    # ─────────────────────────────────────────────────────────────────────

    def record_escalation(self, escalation: AutonomyEscalation) -> None:
        self._escalations.setdefault(escalation.objective_id, []).append(escalation)

    def get_escalations(self, objective_id: str) -> List[AutonomyEscalation]:
        return list(self._escalations.get(objective_id, []))

    def pending_escalation_count(self) -> int:
        count = 0
        for escs in self._escalations.values():
            count += sum(1 for e in escs if e.resolved_at is None)
        return count

    # ─────────────────────────────────────────────────────────────────────
    # Kill Switch
    # ─────────────────────────────────────────────────────────────────────

    def enable_kill_switch(self) -> None:
        self._kill_switch = True
        logger.warning("[Registry] KILL SWITCH ENABLED — all new autonomous actions halted.")

    def disable_kill_switch(self) -> None:
        self._kill_switch = False
        logger.info("[Registry] Kill switch disabled — autonomy resumed.")

    @property
    def kill_switch_active(self) -> bool:
        return self._kill_switch

    # ─────────────────────────────────────────────────────────────────────
    # Health
    # ─────────────────────────────────────────────────────────────────────

    def get_health(self) -> AutonomyHealth:
        from autonomy.models import ObjectiveStatus
        objs = list(self._objectives.values())
        active = sum(1 for o in objs if o.status in [
            ObjectiveStatus.ACTIVE, ObjectiveStatus.EXECUTING,
            ObjectiveStatus.PLANNING, ObjectiveStatus.EVALUATING,
            ObjectiveStatus.REPLANNING
        ])
        blocked = sum(1 for o in objs if o.status == ObjectiveStatus.BLOCKED)
        pending_escs = self.pending_escalation_count()

        if self._kill_switch:
            status = AutonomyHealthStatus.DISABLED
            message = "Kill switch is active. No new autonomous actions."
        elif blocked > 0 or pending_escs > 0:
            status = AutonomyHealthStatus.DEGRADED
            message = f"{blocked} blocked objectives, {pending_escs} pending escalations."
        else:
            status = AutonomyHealthStatus.HEALTHY
            message = "System operational."

        return AutonomyHealth(
            status=status,
            active_objectives=active,
            kill_switch_active=self._kill_switch,
            blocked_objectives=blocked,
            escalations_pending=pending_escs,
            message=message,
        )
