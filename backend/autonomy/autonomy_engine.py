"""
Autonomy Engine (Phase 16)

Top-level orchestration loop for the Autonomous Company.

IMPORTANT: This is NOT a literal while-loop.
advance() is called per-event or per-scheduled-tick and returns one decision.
Callers (event handlers, schedulers, API endpoints) drive the loop.

Control flow per advance() call:
  1. Load objective
  2. Increment iteration counter
  3. Check kill switch → PAUSE if active
  4. Observe current state
  5. Compute progress
  6. Detect loops
  7. Evaluate policy
  8. Produce decision (DecisionEngine)
  9. Check approval gate
  10. Record decision
  11. Execute decision (ActionExecutor)
  12. Update objective status
  13. Return decision

Wakeup events that should call advance():
  - OBJECTIVE_ACTIVATED
  - TASK_COMPLETED
  - TASK_FAILED
  - QUALITY_RESULT_RECEIVED
  - APPROVAL_RECEIVED
  - DEADLINE_APPROACHING
  - SCHEDULED_TICK

Concurrency: Each objective has isolated state. Failure in one
objective MUST NOT affect another.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set

from autonomy.models import (
    CompanyObjective, CompanyPlan, AutonomyDecision, AutonomyPolicy,
    DecisionType, ObjectiveStatus,
)
from autonomy.registry import ObjectiveRegistry
from autonomy.objective_manager import ObjectiveManager
from autonomy.state_observer import CompanyStateObserver
from autonomy.progress_tracker import ProgressTracker
from autonomy.decision_engine import DecisionEngine
from autonomy.loop_detector import LoopDetector
from autonomy.policy_engine import AutonomyPolicyEngine
from autonomy.approval_gate import ApprovalGate
from autonomy.action_executor import AutonomousActionExecutor, ActionExecutionResult

logger = logging.getLogger(__name__)

# Statuses in which advance() should not be called
_NON_ADVANCEABLE = {
    ObjectiveStatus.DRAFT,
    ObjectiveStatus.PAUSED,
    ObjectiveStatus.COMPLETED,
    ObjectiveStatus.FAILED,
    ObjectiveStatus.CANCELLED,
    ObjectiveStatus.EXPIRED,
}


class AutonomyEngine:
    """
    Top-level controller for a single objective's autonomous execution.
    One engine instance is safe to share across multiple advance() calls.
    """

    def __init__(
        self,
        registry: ObjectiveRegistry,
        policy: Optional[AutonomyPolicy] = None,
        task_orchestrator=None,
        talent_market_service=None,
    ):
        self.registry = registry
        self.policy = policy or AutonomyPolicy()

        # Compose focused components
        self.obj_manager      = ObjectiveManager(registry)
        self.observer         = CompanyStateObserver()
        self.progress_tracker = ProgressTracker()
        self.decision_engine  = DecisionEngine()
        self.loop_detector    = LoopDetector()
        self.policy_engine    = AutonomyPolicyEngine()
        self.approval_gate    = ApprovalGate()
        self.executor         = AutonomousActionExecutor(
            registry=registry,
            obj_manager=self.obj_manager,
            task_orchestrator=task_orchestrator,
            talent_market_service=talent_market_service,
        )

    def advance(
        self,
        objective_id: str,
        trigger: str = "SCHEDULED",
        task_states: Optional[Dict[str, str]] = None,
        quality_results: Optional[Dict[str, bool]] = None,
        completed_descriptor_ids: Optional[Set[str]] = None,
        failed_descriptor_ids: Optional[Dict[str, int]] = None,
        task_failure_counts: Optional[Dict[str, int]] = None,
        current_agent_count: int = 0,
        current_task_count: int = 0,
        produced_outputs: Optional[List[str]] = None,
    ) -> Optional[AutonomyDecision]:
        """
        Advance the objective by one decision cycle.
        Returns the decision made (including WAIT decisions).
        Returns None if the objective is in a terminal / non-advanceable state.
        """
        objective = self.registry.get_objective(objective_id)
        if objective is None:
            logger.error(f"[AutonomyEngine] Objective '{objective_id}' not found.")
            return None

        if objective.status in _NON_ADVANCEABLE:
            logger.debug(
                f"[AutonomyEngine] Objective '{objective_id}' is {objective.status} — "
                f"skipping advance."
            )
            return None

        # ── Step 1: Increment iteration ─────────────────────────────────
        self.obj_manager.increment_iteration(objective_id)
        objective = self.registry.get_objective(objective_id)

        # ── Step 2: Load current plan ───────────────────────────────────
        plan: Optional[CompanyPlan] = None
        if objective.current_plan_id:
            plan = self.registry.get_plan(objective.current_plan_id)

        # ── Step 3: Observe state ───────────────────────────────────────
        escalations = self.registry.get_escalations(objective_id)
        snapshot = self.observer.observe(
            objective=objective,
            plan=plan,
            task_states=task_states or {},
            quality_results=quality_results or {},
            escalations=escalations,
        )

        # ── Step 4: Progress ────────────────────────────────────────────
        progress = self.progress_tracker.compute(snapshot)

        # ── Step 5: Loop detection ──────────────────────────────────────
        decisions = self.registry.get_decisions(objective_id)
        loop_result = self.loop_detector.detect(
            decisions=decisions,
            task_failure_counts=task_failure_counts or failed_descriptor_ids or {},
            max_retries_per_task=objective.budget_config.max_retries_per_task,
            max_replan_count=objective.budget_config.max_replan_count,
            current_replan_count=objective.budget_config.replan_count,
        )

        # ── Step 6: Policy check ────────────────────────────────────────
        # Determine likely decision type for policy pre-check
        likely_type = DecisionType.WAIT
        if plan is None:
            likely_type = DecisionType.REPLAN
        policy_result = self.policy_engine.evaluate(
            objective=objective,
            decision_type=likely_type,
            policy=self.policy,
            current_agent_count=current_agent_count,
            current_task_count=current_task_count,
        )

        # ── Step 7: Produce decision ────────────────────────────────────
        pending_approvals = len(self.registry.get_pending_approvals(objective_id))
        decision = self.decision_engine.decide(
            objective=objective,
            plan=plan,
            snapshot=snapshot,
            policy=self.policy,
            trigger=trigger,
            completed_descriptor_ids=completed_descriptor_ids,
            failed_descriptor_ids=failed_descriptor_ids,
            pending_approval_count=pending_approvals,
            loop_result=loop_result,
        )

        # Escalate if policy is violated and decision isn't already ESCALATE/PAUSE
        if not policy_result.allowed and decision.decision_type not in {
            DecisionType.ESCALATE, DecisionType.PAUSE, DecisionType.WAIT
        }:
            from autonomy.models import RiskLevel
            decision.decision_type = DecisionType.ESCALATE
            decision.reason = f"Policy violation: {'; '.join(policy_result.violations)}"
            decision.risk_level = RiskLevel.HIGH

        # ── Step 8: Approval gate ───────────────────────────────────────
        approval = self.approval_gate.check(
            decision_type=decision.decision_type,
            action_category=self.executor._categorize(decision.decision_type),
            risk_level=decision.risk_level,
            autonomy_level=objective.autonomy_level,
            policy=self.policy,
        )
        if approval.required and not decision.requires_approval:
            decision.requires_approval = True
            decision.decision_type = DecisionType.REQUEST_APPROVAL
            decision.reason = (
                f"Action requires approval ({approval.gate_name}): {approval.reason}"
            )

        # ── Step 9: Record decision ─────────────────────────────────────
        self.registry.record_decision(decision)

        # ── Step 10: Execute ────────────────────────────────────────────
        if decision.decision_type != DecisionType.REQUEST_APPROVAL:
            exec_result = self.executor.execute(
                decision=decision,
                objective=objective,
                plan=plan,
                snapshot=snapshot,
                quality_results=quality_results,
                produced_outputs=produced_outputs,
            )
            logger.info(
                f"[AutonomyEngine] '{objective_id}' | trigger={trigger} | "
                f"decision={decision.decision_type.value} | "
                f"success={exec_result.success}"
            )
        else:
            logger.info(
                f"[AutonomyEngine] '{objective_id}' | trigger={trigger} | "
                f"decision=REQUEST_APPROVAL | reason={decision.reason}"
            )

        return decision

    # ─────────────────────────────────────────────────────────────────────
    # Convenience helpers
    # ─────────────────────────────────────────────────────────────────────

    def activate(self, objective_id: str) -> CompanyObjective:
        """Activate a DRAFT objective and trigger initial planning."""
        obj = self.obj_manager.activate(objective_id)
        return obj

    def pause(self, objective_id: str) -> CompanyObjective:
        return self.obj_manager.pause(objective_id)

    def resume(self, objective_id: str) -> CompanyObjective:
        return self.obj_manager.resume(objective_id)

    def cancel(self, objective_id: str) -> CompanyObjective:
        return self.obj_manager.cancel(objective_id)

    def enable_kill_switch(self) -> None:
        self.registry.enable_kill_switch()
        self.policy.kill_switch_active = True

    def disable_kill_switch(self) -> None:
        self.registry.disable_kill_switch()
        self.policy.kill_switch_active = False

    def get_health(self):
        return self.registry.get_health()
