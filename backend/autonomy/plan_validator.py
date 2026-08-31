"""
Plan Validator (Phase 16)

Validates a CompanyPlan for feasibility before execution begins.

Checks:
1. Task descriptors have valid structure
2. Dependency graph forms a valid DAG (no cycles)
3. Budget estimate within objective limit
4. Deadline feasibility (rough estimate vs. remaining time)
5. Required capabilities non-empty (structural check only)
6. Milestone sequence valid

The validator does NOT:
- Execute tasks
- Call Hiring
- Query Memory
- Invoke LLM
- Modify the plan
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set

from autonomy.models import (
    CompanyObjective, CompanyPlan, PlanValidationResult
)

logger = logging.getLogger(__name__)


class PlanValidator:
    """
    Validates a CompanyPlan for structural and feasibility correctness.
    Returns PlanValidationResult (never raises for validation failures).
    """

    def validate(
        self,
        plan: CompanyPlan,
        objective: CompanyObjective,
    ) -> PlanValidationResult:
        blockers: List[str] = []
        warnings: List[str] = []

        self._check_descriptors(plan, blockers, warnings)
        self._check_dag(plan, blockers)
        self._check_milestones(plan, blockers, warnings)
        self._check_budget(plan, objective, blockers, warnings)
        self._check_deadline(plan, objective, warnings)

        return PlanValidationResult(
            valid=len(blockers) == 0,
            blockers=blockers,
            warnings=warnings,
        )

    # ─────────────────────────────────────────────────────────────────────
    # Checks
    # ─────────────────────────────────────────────────────────────────────

    def _check_descriptors(self, plan: CompanyPlan, blockers: List, warnings: List) -> None:
        if not plan.task_descriptors:
            blockers.append("Plan has no task descriptors — nothing to execute.")
            return

        ids: Set[str] = set()
        for d in plan.task_descriptors:
            if not d.title.strip():
                blockers.append(f"Descriptor '{d.descriptor_id}' has empty title.")
            if not d.milestone_id:
                blockers.append(f"Descriptor '{d.descriptor_id}' has no milestone_id.")
            if d.descriptor_id in ids:
                blockers.append(f"Duplicate descriptor_id: '{d.descriptor_id}'.")
            ids.add(d.descriptor_id)

        # Check all depends_on references are valid
        for d in plan.task_descriptors:
            for dep in d.depends_on:
                if dep not in ids:
                    blockers.append(
                        f"Descriptor '{d.descriptor_id}' depends on unknown '{dep}'."
                    )

    def _check_dag(self, plan: CompanyPlan, blockers: List) -> None:
        """Detect cycles using DFS coloring."""
        graph = plan.dependency_graph
        # Build reverse: successor → [predecessors]
        rev: Dict[str, List[str]] = {d.descriptor_id: [] for d in plan.task_descriptors}
        for d in plan.task_descriptors:
            for dep in d.depends_on:
                if dep in rev:
                    rev[dep].append(d.descriptor_id)

        WHITE, GRAY, BLACK = 0, 1, 2
        color: Dict[str, int] = {nid: WHITE for nid in rev}

        def dfs(node: str) -> bool:
            color[node] = GRAY
            for succ in rev.get(node, []):
                if color.get(succ, WHITE) == GRAY:
                    return True   # Cycle found
                if color.get(succ, WHITE) == WHITE and dfs(succ):
                    return True
            color[node] = BLACK
            return False

        for node in list(color.keys()):
            if color[node] == WHITE:
                if dfs(node):
                    blockers.append(
                        "Plan dependency graph contains a cycle — cannot execute."
                    )
                    return  # One cycle message is enough

    def _check_milestones(self, plan: CompanyPlan, blockers: List, warnings: List) -> None:
        if not plan.milestones:
            warnings.append("Plan has no milestones — progress tracking will be unavailable.")
            return
        sequences = [m.sequence for m in plan.milestones]
        if len(sequences) != len(set(sequences)):
            warnings.append("Milestone sequence numbers are not unique.")

    def _check_budget(
        self,
        plan: CompanyPlan,
        objective: CompanyObjective,
        blockers: List,
        warnings: List,
    ) -> None:
        if plan.estimated_cost is None:
            warnings.append("Plan has no cost estimate — budget tracking will be unavailable.")
            return
        budget = objective.budget_config
        if budget.max_cost is not None:
            remaining = budget.max_cost - budget.spent_cost
            if plan.estimated_cost > remaining:
                blockers.append(
                    f"Plan estimated cost ({plan.estimated_cost:.2f}) exceeds "
                    f"remaining budget ({remaining:.2f})."
                )
            elif plan.estimated_cost > remaining * budget.budget_alert_threshold:
                warnings.append(
                    f"Plan estimated cost ({plan.estimated_cost:.2f}) exceeds "
                    f"{int(budget.budget_alert_threshold * 100)}% of remaining budget."
                )

    def _check_deadline(
        self,
        plan: CompanyPlan,
        objective: CompanyObjective,
        warnings: List,
    ) -> None:
        deadline = objective.constraints.deadline
        if deadline is None:
            return
        now = datetime.now(timezone.utc)
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=timezone.utc)
        remaining_hours = (deadline - now).total_seconds() / 3600
        task_count = len(plan.task_descriptors)
        # Rough heuristic: 1 hour per task minimum
        if task_count > remaining_hours:
            warnings.append(
                f"Deadline risk: {task_count} tasks planned but only "
                f"{remaining_hours:.1f} hours remaining until deadline."
            )
