"""
Task Plan Validator & Dependency Validator (Phase 10 Task Orchestration)

Responsibilities:
- Deterministic DAG cycle detection for WorkUnit dependencies.
- Validates team existence against TeamRegistry.
- Validates pipeline existence and ownership against PipelineRegistry.
- Validates execution contract existence and ownership against ExecutionContractRegistry.
- Validates cross-team collaboration contracts against TeamCollaborationContractRegistry.
- Validates output contracts and expected deliverables.
- Computes plan status (READY, READY_WITH_WARNINGS, BLOCKED, INVALID).
- Does NOT rely on LLM for validation.
"""

import logging
from typing import List, Dict, Set, Tuple, Optional

from tasks.models import (
    TaskPlan,
    TaskPlanStatus,
    WorkUnit,
    WorkUnitDependency,
    PlanBlocker,
    PlanWarning,
    BlockerCode,
)

from teams.registry import TeamRegistry
from execution.pipelines.registry import PipelineRegistry
from execution.contracts.registry import ExecutionContractRegistry
from execution.collaboration.registry import TeamCollaborationContractRegistry

logger = logging.getLogger(__name__)


class DependencyValidator:
    """Validates dependency graphs between WorkUnits (cycle detection, DAG check)."""

    def validate_dependencies(
        self, work_units: List[WorkUnit], dependencies: List[WorkUnitDependency]
    ) -> List[PlanBlocker]:
        blockers: List[PlanBlocker] = []
        wu_ids = {wu.work_unit_id for wu in work_units}

        # 1. Unknown WorkUnit reference check
        for dep in dependencies:
            if dep.from_work_unit_id not in wu_ids:
                blockers.append(
                    PlanBlocker(
                        code=BlockerCode.INVALID_DEPENDENCY,
                        message=f"Dependency reference from_work_unit_id '{dep.from_work_unit_id}' does not exist.",
                        severity="ERROR",
                    )
                )
            if dep.to_work_unit_id not in wu_ids:
                blockers.append(
                    PlanBlocker(
                        code=BlockerCode.INVALID_DEPENDENCY,
                        message=f"Dependency reference to_work_unit_id '{dep.to_work_unit_id}' does not exist.",
                        severity="ERROR",
                    )
                )
            if dep.from_work_unit_id == dep.to_work_unit_id:
                blockers.append(
                    PlanBlocker(
                        code=BlockerCode.INVALID_DEPENDENCY,
                        message=f"Self-referencing dependency detected on '{dep.from_work_unit_id}'.",
                        severity="ERROR",
                    )
                )

        if blockers:
            return blockers

        # 2. Cycle Detection (DFS for DAG validation)
        adj: Dict[str, List[str]] = {wu_id: [] for wu_id in wu_ids}
        for dep in dependencies:
            # dep.from_work_unit_id must run BEFORE dep.to_work_unit_id
            adj[dep.from_work_unit_id].append(dep.to_work_unit_id)

        visited: Dict[str, int] = {wu_id: 0 for wu_id in wu_ids}  # 0=unvisited, 1=visiting, 2=visited

        def has_cycle(node: str) -> bool:
            visited[node] = 1
            for neighbor in adj.get(node, []):
                if visited[neighbor] == 1:
                    return True
                if visited[neighbor] == 0 and has_cycle(neighbor):
                    return True
            visited[node] = 2
            return False

        for wu_id in wu_ids:
            if visited[wu_id] == 0:
                if has_cycle(wu_id):
                    blockers.append(
                        PlanBlocker(
                            code=BlockerCode.INVALID_EXECUTION_GRAPH,
                            message="Dependency cycle detected in execution graph. Execution graph must be a DAG.",
                            severity="ERROR",
                        )
                    )
                    break

        return blockers


class TaskPlanValidator:
    """
    Deterministic validator for TaskPlan.
    Validates against actual system registries.
    """

    def __init__(
        self,
        team_registry: TeamRegistry,
        pipeline_registry: PipelineRegistry,
        execution_contracts: ExecutionContractRegistry,
        collaboration_contracts: TeamCollaborationContractRegistry,
    ):
        self._teams = team_registry
        self._pipelines = pipeline_registry
        self._exec_contracts = execution_contracts
        self._collab_contracts = collaboration_contracts
        self._dep_validator = DependencyValidator()

    def validate_plan(self, plan: TaskPlan) -> TaskPlan:
        """
        Validates TaskPlan against registries and returns updated TaskPlan with status & blockers/warnings.
        """
        blockers: List[PlanBlocker] = []
        warnings: List[PlanWarning] = []

        # ── 1. Validate WorkUnit count ────────────────────────────────────
        if not plan.work_units:
            blockers.append(
                PlanBlocker(
                    code=BlockerCode.NO_CAPABLE_TEAM,
                    message="TaskPlan contains zero work units.",
                    severity="ERROR",
                )
            )
            plan.blockers = blockers
            plan.status = TaskPlanStatus.INVALID
            return plan

        # ── 2. Validate Dependencies & Cycles ─────────────────────────────
        dep_blockers = self._dep_validator.validate_dependencies(
            plan.work_units, plan.dependencies
        )
        blockers.extend(dep_blockers)

        # ── 3. Validate WorkUnits ─────────────────────────────────────────
        for wu in plan.work_units:
            # Team existence
            if not self._teams.exists(wu.team_id):
                blockers.append(
                    PlanBlocker(
                        code=BlockerCode.NO_CAPABLE_TEAM,
                        message=f"WorkUnit '{wu.work_unit_id}' references unknown team '{wu.team_id}'.",
                        work_unit_id=wu.work_unit_id,
                        team_id=wu.team_id,
                    )
                )

            # Pipeline existence & ownership
            if wu.pipeline_id:
                pipe = getattr(self._pipelines, "get_pipeline", getattr(self._pipelines, "get", lambda x: None))(wu.pipeline_id)
                if not pipe:
                    blockers.append(
                        PlanBlocker(
                            code=BlockerCode.MISSING_PIPELINE,
                            message=f"Pipeline '{wu.pipeline_id}' not found in PipelineRegistry.",
                            work_unit_id=wu.work_unit_id,
                            team_id=wu.team_id,
                        )
                    )
                elif pipe.team_id != wu.team_id:
                    blockers.append(
                        PlanBlocker(
                            code=BlockerCode.MISSING_PIPELINE,
                            message=(
                                f"Pipeline '{wu.pipeline_id}' belongs to team '{pipe.team_id}', "
                                f"not WorkUnit team '{wu.team_id}'."
                            ),
                            work_unit_id=wu.work_unit_id,
                            team_id=wu.team_id,
                        )
                    )

            # Execution Contract existence & ownership
            if wu.execution_contract_id:
                contract = self._exec_contracts.get(wu.execution_contract_id)
                if not contract:
                    blockers.append(
                        PlanBlocker(
                            code=BlockerCode.MISSING_EXECUTION_CONTRACT,
                            message=f"Execution contract '{wu.execution_contract_id}' not found.",
                            work_unit_id=wu.work_unit_id,
                            team_id=wu.team_id,
                        )
                    )
                elif contract.team_id != wu.team_id:
                    blockers.append(
                        PlanBlocker(
                            code=BlockerCode.INVALID_EXECUTION_CONTRACT,
                            message=(
                                f"Contract '{wu.execution_contract_id}' belongs to team '{contract.team_id}', "
                                f"not WorkUnit team '{wu.team_id}'."
                            ),
                            work_unit_id=wu.work_unit_id,
                            team_id=wu.team_id,
                        )
                    )

            # Outputs validation
            if not wu.expected_outputs:
                blockers.append(
                    PlanBlocker(
                        code=BlockerCode.MISSING_OUTPUT,
                        message=f"WorkUnit '{wu.work_unit_id}' has no declared expected outputs.",
                        work_unit_id=wu.work_unit_id,
                        team_id=wu.team_id,
                    )
                )

        # ── 4. Cross-Team Collaboration Validation ───────────────────────
        wu_map = {wu.work_unit_id: wu for wu in plan.work_units}
        for dep in plan.dependencies:
            wu_from = wu_map.get(dep.from_work_unit_id)
            wu_to = wu_map.get(dep.to_work_unit_id)

            if wu_from and wu_to and wu_from.team_id != wu_to.team_id:
                # Cross-team dependency requires Collaboration Contract
                # wu_from is provider, wu_to is requester
                collab_contracts = self._collab_contracts.get_by_providing_team(wu_from.team_id)
                matching = [c for c in collab_contracts if c.requesting_team_id == wu_to.team_id]

                if not matching:
                    warnings.append(
                        PlanWarning(
                            code="COLLABORATION_CONTRACT_WARNING",
                            message=(
                                f"Cross-team dependency between '{wu_from.team_id}' and '{wu_to.team_id}' "
                                f"has no explicit registered CollaborationContract."
                            ),
                            work_unit_id=wu_to.work_unit_id,
                        )
                    )
                else:
                    wu_to.collaboration_contract_id = matching[0].contract_id

        # ── 5. Compute Final Plan Status ──────────────────────────────────
        plan.blockers = blockers
        plan.warnings = warnings

        if blockers:
            plan.status = TaskPlanStatus.INVALID
        elif warnings:
            plan.status = TaskPlanStatus.READY
        else:
            plan.status = TaskPlanStatus.READY

        return plan
