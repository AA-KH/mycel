"""
Task Planner (Phase 10 Task Orchestration)

Responsibilities:
- Assembles TaskOutcome, WorkUnits, Team Resolution, and Dependencies into a versioned TaskPlan.
- Identifies sequential vs parallel relationships between WorkUnits.
- Builds DAG of WorkUnitDependency objects.
- Passes assembled plan to TaskPlanValidator for deterministic registry validation.
- Does NOT perform employee hiring or agent runtime creation.
"""

import uuid
import logging
from typing import List, Dict, Any, Optional

from tasks.models import (
    Task,
    TaskOutcome,
    WorkUnit,
    WorkUnitDependency,
    DependencyType,
    TaskPlan,
    TaskPlanStatus,
)
from tasks.resolver import TeamResolver
from tasks.validator import TaskPlanValidator

logger = logging.getLogger(__name__)

# Standard cross-team flow ordering priority
TEAM_ORDER_PRIORITY = {
    "research": 1,
    "finance": 1,
    "legal": 2,
    "operations": 2,
    "developer": 3,
    "creative": 4,
    "marketing": 5,
}


class TaskPlanner:
    """
    Constructs and validates versioned TaskPlans.
    """

    def __init__(
        self,
        team_resolver: TeamResolver,
        validator: TaskPlanValidator,
    ):
        self._resolver = team_resolver
        self._validator = validator

    def build_plan(
        self,
        task: Task,
        outcome: TaskOutcome,
        work_units: List[WorkUnit],
        version: int = 1,
    ) -> TaskPlan:
        """
        Builds a versioned TaskPlan from TaskOutcome and proposed WorkUnits.
        """
        plan_id = f"plan_{task.task_id[:8]}_v{version}"
        resolved_units: List[WorkUnit] = []

        # ── 1. Resolve Contracts & Pipelines for each WorkUnit ────────────
        for wu in work_units:
            res = self._resolver.resolve_team_for_task_type(
                task_type=wu.expected_outputs[0] if wu.expected_outputs else "standard_task",
                required_capabilities=wu.required_capabilities,
                preferred_team_id=wu.team_id,
            )

            if res and res.valid:
                wu.team_id = res.team_id
                wu.execution_contract_id = res.execution_contract.contract_id if res.execution_contract else None
                wu.pipeline_id = res.pipeline_id
            resolved_units.append(wu)

        # ── 2. Build Dependency Graph between WorkUnits ────────────────────
        dependencies = self._build_dependencies(task.task_id, resolved_units)

        # ── 3. Flag Parallelizable Units ──────────────────────────────────
        dependent_to_ids = {dep.to_work_unit_id for dep in dependencies}
        for wu in resolved_units:
            if wu.work_unit_id not in dependent_to_ids and len(resolved_units) > 1:
                wu.parallelizable = True

        # ── 4. Assemble Draft TaskPlan ─────────────────────────────────────
        completion_criteria = [
            f"All {len(resolved_units)} work units completed successfully.",
            f"Deliverable outputs [{', '.join(outcome.required_outputs)}] generated.",
        ]

        failure_conditions = [
            "Any work unit fails execution contract criteria.",
            "Required output artifact is missing or invalid.",
            "Cross-team dependency handoff fails validation.",
        ]

        draft_plan = TaskPlan(
            plan_id=plan_id,
            task_id=task.task_id,
            version=version,
            status=TaskPlanStatus.DRAFT,
            objective=outcome.objective,
            work_units=resolved_units,
            dependencies=dependencies,
            expected_outputs=outcome.required_outputs,
            completion_criteria=completion_criteria,
            failure_conditions=failure_conditions,
        )

        # ── 5. Deterministic Registry Validation ──────────────────────────
        validated_plan = self._validator.validate_plan(draft_plan)
        return validated_plan

    def _build_dependencies(
        self, task_id: str, work_units: List[WorkUnit]
    ) -> List[WorkUnitDependency]:
        """
        Derives dependencies based on canonical team ordering (e.g. Research -> Creative).
        """
        dependencies: List[WorkUnitDependency] = []
        if len(work_units) <= 1:
            return dependencies

        # Sort units by canonical flow priority
        sorted_units = sorted(
            work_units,
            key=lambda u: TEAM_ORDER_PRIORITY.get(u.team_id, 99)
        )

        for i in range(len(sorted_units) - 1):
            wu_prev = sorted_units[i]
            wu_next = sorted_units[i + 1]

            # If previous team is higher priority (runs earlier), add sequential dependency
            p_prev = TEAM_ORDER_PRIORITY.get(wu_prev.team_id, 99)
            p_next = TEAM_ORDER_PRIORITY.get(wu_next.team_id, 99)

            if p_prev < p_next:
                dep_id = f"dep_{wu_prev.work_unit_id}_to_{wu_next.work_unit_id}"
                dep = WorkUnitDependency(
                    dependency_id=dep_id,
                    task_id=task_id,
                    from_work_unit_id=wu_prev.work_unit_id,
                    to_work_unit_id=wu_next.work_unit_id,
                    dependency_type=DependencyType.OUTPUT_REQUIRED,
                    required=True,
                    description=f"{wu_next.team_id.title()} work depends on outputs from {wu_prev.team_id.title()}.",
                )
                dependencies.append(dep)
                wu_next.dependencies.append(wu_prev.work_unit_id)

        return dependencies
