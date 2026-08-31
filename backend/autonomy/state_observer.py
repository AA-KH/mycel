"""
Company State Observer (Phase 16)

Builds a lightweight CompanyStateSnapshot from injected live system state.

The observer does NOT:
- Query MongoDB directly
- Load all employees
- Load all memory
- Duplicate source systems
- Call LLM

It accepts pre-fetched summaries from existing systems (dependency injection)
and assembles them into a snapshot.  This keeps it testable and decoupled.

Input protocol:
  observe(
    objective,
    plan,
    task_states:     Dict[task_id, status_str],
    quality_results: Dict[task_id, passed: bool],
    budget_state:    Dict (from AutonomyBudget),
    escalations:     List[AutonomyEscalation],
  ) → CompanyStateSnapshot
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

from autonomy.models import (
    CompanyObjective, CompanyPlan, CompanyStateSnapshot,
    MilestoneProgress, MilestoneStatus, AutonomyEscalation,
)

logger = logging.getLogger(__name__)

# Task status strings that count as "completed" for progress purposes
_COMPLETED_STATUSES = {"COMPLETED"}
_FAILED_STATUSES    = {"FAILED", "CANCELLED"}
_ACTIVE_STATUSES    = {"EXECUTING", "READY_FOR_EXECUTION", "ANALYZING", "PLANNING"}
_BLOCKED_STATUSES   = {"BLOCKED", "WAITING_FOR_INPUT"}


class CompanyStateObserver:
    """
    Assembles CompanyStateSnapshot from injected system state summaries.
    Stateless — safe to reuse across objectives.
    """

    def observe(
        self,
        objective: CompanyObjective,
        plan: Optional[CompanyPlan],
        task_states: Dict[str, str],        # task_id → TaskStatus.value
        quality_results: Dict[str, bool],   # task_id → passed
        budget_override: Optional[Dict] = None,
        escalations: Optional[List[AutonomyEscalation]] = None,
    ) -> CompanyStateSnapshot:
        """
        Build a snapshot from injected state.

        task_states     : task_id → status string (from Task.status.value)
        quality_results : task_id → True if QG passed, False if failed
                          Missing key = not yet evaluated
        budget_override : Optional dict to override budget fields
        escalations     : Active escalations for this objective
        """
        escalations = escalations or []

        snap = CompanyStateSnapshot(
            objective_id=objective.objective_id,
            plan_version=plan.version if plan else 0,
        )

        # 1. Task counts
        for task_id, status in task_states.items():
            if status in _ACTIVE_STATUSES:
                snap.active_task_count += 1
            elif status in _COMPLETED_STATUSES:
                # Count as completed only if quality passed (or not yet evaluated)
                q_passed = quality_results.get(task_id)
                if q_passed is None or q_passed:
                    snap.completed_task_count += 1
                else:
                    snap.failed_task_count += 1    # Completed but QG failed
            elif status in _FAILED_STATUSES:
                snap.failed_task_count += 1
            elif status in _BLOCKED_STATUSES:
                snap.blocked_task_count += 1

        # 2. Milestone progress
        if plan:
            milestone_progress = []
            total_weight = 0.0
            weighted_completion = 0.0

            for ms in plan.milestones:
                ms_task_ids = ms.task_ids
                total = len(ms_task_ids)
                completed = 0
                failed = 0

                for tid in ms_task_ids:
                    s = task_states.get(tid, "CREATED")
                    qp = quality_results.get(tid)
                    if s in _COMPLETED_STATUSES and (qp is None or qp):
                        completed += 1
                    elif s in _FAILED_STATUSES or (s in _COMPLETED_STATUSES and qp is False):
                        failed += 1

                pct = (completed / total) if total > 0 else 0.0

                # Determine milestone status
                if completed == total and total > 0:
                    ms_status = MilestoneStatus.COMPLETED
                elif completed > 0 or snap.active_task_count > 0:
                    ms_status = MilestoneStatus.IN_PROGRESS
                elif failed > 0:
                    ms_status = MilestoneStatus.FAILED
                else:
                    ms_status = MilestoneStatus.PENDING

                milestone_progress.append(MilestoneProgress(
                    milestone_id=ms.milestone_id,
                    title=ms.title,
                    status=ms_status,
                    total_tasks=total,
                    completed_tasks=completed,
                    failed_tasks=failed,
                    progress_pct=round(pct, 2),
                ))

                # Equal weight per milestone for overall progress
                total_weight += 1.0
                weighted_completion += pct

            snap.milestone_progress = milestone_progress
            snap.overall_progress = round(
                (weighted_completion / total_weight) if total_weight > 0 else 0.0, 2
            )

        # 3. Budget state
        budget = objective.budget_config
        snap.budget_state = {
            "max_cost": budget.max_cost,
            "spent_cost": budget.spent_cost,
            "cost_exhausted": budget.cost_exhausted,
            "cost_alert": budget.cost_alert,
            "iterations_used": budget.current_iterations,
            "max_iterations": budget.max_iterations,
            "tasks_created": budget.tasks_created,
            "max_tasks": budget.max_tasks,
            "replan_count": budget.replan_count,
            "max_replan_count": budget.max_replan_count,
        }
        if budget_override:
            snap.budget_state.update(budget_override)

        # 4. Quality state summary
        total_evaluated = len(quality_results)
        passed = sum(1 for v in quality_results.values() if v)
        snap.quality_state = {
            "evaluated": total_evaluated,
            "passed": passed,
            "failed": total_evaluated - passed,
            "pass_rate": round(passed / total_evaluated, 2) if total_evaluated > 0 else None,
        }

        # 5. Blockers and escalations
        if snap.blocked_task_count > 0:
            snap.active_blockers.append(f"{snap.blocked_task_count} blocked tasks.")
        if budget.cost_exhausted:
            snap.active_blockers.append("Budget exhausted.")
        if budget.iterations_exhausted:
            snap.active_blockers.append("Iteration limit reached.")

        active_escs = [e for e in escalations if e.resolved_at is None]
        snap.has_escalation = len(active_escs) > 0
        if snap.has_escalation:
            snap.active_blockers.append(f"{len(active_escs)} pending escalation(s).")

        snap.last_evaluated_at = datetime.now(timezone.utc)
        return snap
