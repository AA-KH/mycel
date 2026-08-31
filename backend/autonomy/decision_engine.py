"""
Decision Engine (Phase 16)

Produces AutonomyDecisions from the current objective state.
Every decision has a reason, evidence, and trigger — no black-box autonomy.

Decision Priority:
  1. SAFETY   — kill switch, policy violations → PAUSE/CANCEL/ESCALATE
  2. POLICY   — budget, concurrency, permission checks → REQUEST_APPROVAL/PAUSE
  3. BLOCKERS — loop detection, escalations → ESCALATE
  4. DEADLINES — deadline risk → REPLAN
  5. QUALITY  — quality failures → RETRY/REPLAN
  6. PROGRESS — completed tasks → advance to next descriptor → CREATE_TASK
  7. COST     — optimization (minimize cost, prefer existing resources)

Output: AutonomyDecision (always — even if WAIT)

The decision engine does NOT:
- Execute tasks
- Call LLM
- Modify policies
- Grant permissions
- Create agents directly
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set

from autonomy.models import (
    CompanyObjective, CompanyPlan, CompanyStateSnapshot,
    AutonomyDecision, AutonomyPolicy, DecisionType, RiskLevel,
    ActionCategory,
)

logger = logging.getLogger(__name__)


class DecisionEngine:
    """
    Produces the next AutonomyDecision from objective state.
    Stateless — safe to reuse across objectives.
    """

    def decide(
        self,
        objective: CompanyObjective,
        plan: Optional[CompanyPlan],
        snapshot: CompanyStateSnapshot,
        policy: AutonomyPolicy,
        trigger: str = "SCHEDULED",
        completed_descriptor_ids: Optional[Set[str]] = None,
        failed_descriptor_ids: Optional[Dict[str, int]] = None,  # id → fail count
        active_descriptor_ids: Optional[Set[str]] = None,
        pending_approval_count: int = 0,
        loop_result: Optional[Dict] = None,
    ) -> AutonomyDecision:
        """
        Evaluate current state and return the next decision.
        """
        completed = completed_descriptor_ids or set()
        failed = failed_descriptor_ids or {}
        loop_result = loop_result or {"loop_detected": False}

        # ── Priority 1: SAFETY ──────────────────────────────────────────
        if policy.kill_switch_active:
            return self._decision(
                objective, plan,
                DecisionType.PAUSE, trigger,
                reason="Kill switch is active. Pausing all autonomous actions.",
                evidence={"kill_switch": True},
                risk_level=RiskLevel.CRITICAL,
            )

        # ── Priority 2: LOOP / ESCALATION ──────────────────────────────
        if loop_result.get("loop_detected"):
            return self._decision(
                objective, plan,
                DecisionType.ESCALATE, trigger,
                reason=loop_result.get("reason", "Loop detected."),
                evidence={"loop_pattern": loop_result.get("pattern")},
                risk_level=RiskLevel.HIGH,
            )

        if snapshot.has_escalation:
            return self._decision(
                objective, plan,
                DecisionType.WAIT, trigger,
                reason="Pending escalation requires human resolution before continuing.",
                evidence={"active_blockers": snapshot.active_blockers},
                risk_level=RiskLevel.MEDIUM,
            )

        # ── Priority 3: BUDGET ──────────────────────────────────────────
        budget = objective.budget_config
        if budget.cost_exhausted:
            return self._decision(
                objective, plan,
                DecisionType.REQUEST_APPROVAL, trigger,
                reason="Cost budget exhausted. Requesting approval to continue or pause.",
                evidence={"spent": budget.spent_cost, "max": budget.max_cost},
                risk_level=RiskLevel.HIGH,
                requires_approval=True,
            )

        if budget.iterations_exhausted:
            return self._decision(
                objective, plan,
                DecisionType.ESCALATE, trigger,
                reason=f"Iteration limit {budget.max_iterations} reached.",
                evidence={"iterations": budget.current_iterations},
                risk_level=RiskLevel.HIGH,
            )

        # ── Priority 4: PLAN REQUIRED ───────────────────────────────────
        if plan is None:
            return self._decision(
                objective, plan,
                DecisionType.REPLAN, trigger,
                reason="No active plan exists. Creating initial plan.",
                evidence={"plan_id": None},
                risk_level=RiskLevel.LOW,
            )

        # ── Priority 5: ALL SUCCESS CRITERIA MET → COMPLETE ────────────
        if snapshot.overall_progress >= 1.0 and not snapshot.active_blockers:
            return self._decision(
                objective, plan,
                DecisionType.COMPLETE, trigger,
                reason="All milestones completed with quality gates passed. Requesting completion validation.",
                evidence={"progress": snapshot.overall_progress},
                risk_level=RiskLevel.LOW,
            )

        # ── Priority 6: FAILED TASKS ────────────────────────────────────
        if snapshot.failed_task_count > 0 and failed:
            # Check if replan is warranted
            all_failed_once = all(c >= 1 for c in failed.values())
            if all_failed_once:
                return self._decision(
                    objective, plan,
                    DecisionType.REPLAN, trigger,
                    reason=f"{snapshot.failed_task_count} task(s) failed. Replanning.",
                    evidence={"failed_tasks": list(failed.keys())[:5]},
                    risk_level=RiskLevel.MEDIUM,
                )

        # ── Priority 7: BLOCKED ─────────────────────────────────────────
        if snapshot.blocked_task_count > 0 and snapshot.active_task_count == 0:
            return self._decision(
                objective, plan,
                DecisionType.ESCALATE, trigger,
                reason=f"{snapshot.blocked_task_count} task(s) blocked with no active tasks.",
                evidence={"blockers": snapshot.active_blockers},
                risk_level=RiskLevel.HIGH,
            )

        # ── Priority 8: WAITING ON ACTIVE TASKS ─────────────────────────
        if snapshot.active_task_count > 0 and pending_approval_count == 0:
            # Find next available descriptor to queue
            next_desc = self._next_ready_descriptor(plan, completed, failed, active_descriptor_ids or set())
            if next_desc is None:
                return self._decision(
                    objective, plan,
                    DecisionType.WAIT, trigger,
                    reason=f"{snapshot.active_task_count} task(s) still executing.",
                    evidence={"active_count": snapshot.active_task_count},
                    risk_level=RiskLevel.LOW,
                )

        # ── Priority 9: CREATE NEXT TASK ────────────────────────────────
        next_desc = self._next_ready_descriptor(plan, completed, failed, active_descriptor_ids or set())
        if next_desc:
            return self._decision(
                objective, plan,
                DecisionType.CREATE_TASK, trigger,
                reason=f"Dependencies satisfied. Creating task: '{next_desc}'.",
                evidence={"descriptor_id": next_desc},
                risk_level=RiskLevel.LOW,
                target_descriptor_id=next_desc,
            )

        # ── Priority 10: WAIT (no work to do right now) ─────────────────
        return self._decision(
            objective, plan,
            DecisionType.WAIT, trigger,
            reason="No actionable work units ready. Waiting for task completion or new events.",
            evidence={"progress": snapshot.overall_progress},
            risk_level=RiskLevel.LOW,
        )

    # ─────────────────────────────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────────────────────────────

    def _next_ready_descriptor(
        self,
        plan: CompanyPlan,
        completed: Set[str],
        failed: Dict[str, int],
        active: Set[str],
    ) -> Optional[str]:
        """
        Returns the first descriptor whose dependencies are all completed,
        that hasn't been started, completed, or failed.
        """
        in_play = completed | set(failed.keys()) | active
        for desc in plan.task_descriptors:
            if desc.descriptor_id in in_play:
                continue  # Already handled
            # Check all dependencies are completed
            if all(dep in completed for dep in desc.depends_on):
                return desc.descriptor_id
        return None

    def _decision(
        self,
        objective: CompanyObjective,
        plan: Optional[CompanyPlan],
        decision_type: DecisionType,
        trigger: str,
        reason: str,
        evidence: Dict,
        risk_level: RiskLevel = RiskLevel.LOW,
        requires_approval: bool = False,
        target_descriptor_id: Optional[str] = None,
    ) -> AutonomyDecision:
        return AutonomyDecision(
            objective_id=objective.objective_id,
            plan_version=plan.version if plan else 0,
            decision_type=decision_type,
            reason=reason,
            evidence=evidence,
            trigger=trigger,
            risk_level=risk_level,
            requires_approval=requires_approval,
            target_descriptor_id=target_descriptor_id,
        )
