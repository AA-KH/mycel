"""
Task Orchestrator (Phase 10 Task Orchestration Service)

Coordinates the complete Task Orchestration pipeline:
1. Task Creation & Request Normalization (TaskAnalyzer)
2. Outcome & Capability Analysis (CapabilityRequirementResolver)
3. Team & Contract Resolution (TeamResolver)
4. WorkUnit Decomposition (TaskDecomposer)
5. Plan Assembly & Dependency Building (TaskPlanner)
6. Deterministic Validation (TaskPlanValidator)

Strict Boundaries:
- Stops at READY_FOR_EXECUTION.
- Does NOT execute LLM code or pipelines.
- Does NOT hire employees or create agents.
- Does NOT run tools or generate physical artifacts.
"""

import uuid
import logging
from typing import Dict, Optional, List
from datetime import datetime, timezone

from tasks.models import (
    Task,
    TaskStatus,
    TaskRequest,
    TaskOutcome,
    TaskContext,
    TaskConstraints,
    TaskPlan,
    TaskPlanStatus,
    TaskOrchestrationResult,
    TaskClarification,
    ClarificationStatus,
)
from tasks.analyzer import TaskAnalyzer
from tasks.resolver import CapabilityRequirementResolver, TeamResolver
from tasks.decomposer import TaskDecomposer
from tasks.planner import TaskPlanner
from teams.registry import TeamRegistry
from execution.pipelines.registry import PipelineRegistry
from execution.contracts.registry import ExecutionContractRegistry
from execution.collaboration.registry import TeamCollaborationContractRegistry
from teams.resolver import TeamCapabilityResolver
from teams.validator import TeamValidator
from tools.registry.core import registry as tool_registry
from tasks.output_resolver import OutputResolver
from tasks.tool_resolver import ToolResolver

logger = logging.getLogger(__name__)


class TaskOrchestrator:
    """
    Facade service orchestrating task analysis, decomposition, team resolution,
    and plan validation.
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

        # Subservices
        self._capability_resolver = TeamCapabilityResolver(team_registry, pipeline_registry)
        self._analyzer = TaskAnalyzer()
        self._output_resolver = OutputResolver()
        self._tool_resolver = ToolResolver(tool_registry)
        self._cap_resolver = CapabilityRequirementResolver()
        self._team_resolver = TeamResolver(
            self._capability_resolver, self._exec_contracts, self._pipelines
        )
        self._decomposer = TaskDecomposer()

        from tasks.validator import TaskPlanValidator
        self._validator = TaskPlanValidator(
            team_registry, pipeline_registry, execution_contracts, collaboration_contracts
        )
        self._planner = TaskPlanner(self._team_resolver, self._validator)

        # In-memory storage (can be backed by MongoDB repo if present)
        self._tasks: Dict[str, Task] = {}
        self._plans: Dict[str, TaskPlan] = {}
        self._clarifications: Dict[str, TaskClarification] = {}

    def orchestrate_task(
        self,
        user_input: str,
        organization_id: str = "mycel_global",
        context: Optional[TaskContext] = None,
        constraints: Optional[TaskConstraints] = None,
        task_id: Optional[str] = None,
    ) -> TaskOrchestrationResult:
        """
        Main entry point for Task Orchestration.
        Converts user_input -> validated TaskPlan.
        """
        tid = task_id or f"task_{uuid.uuid4().hex[:8]}"
        ctx = context or TaskContext()
        cst = constraints or TaskConstraints()

        # ── Step 1: Create Task Request ───────────────────────────────────
        request = TaskRequest(
            request_id=f"req_{uuid.uuid4().hex[:8]}",
            task_id=tid,
            user_input=user_input,
            context=ctx,
            constraints=cst,
        )

        # ── Step 2: Task Analysis & Normalization ─────────────────────────
        normalized = self._analyzer.normalize_request(user_input)
        outcome, clarifications = self._analyzer.analyze_task(request)
        
        # ── Step 2b: Output Resolution ────────────────────────────────────
        outcome = self._output_resolver.resolve(outcome)

        # Create primary Task entity
        task = Task(
            task_id=tid,
            organization_id=organization_id,
            title=outcome.objective[:80] if outcome.objective else "Untitled Task",
            description=outcome.intent,
            original_request=user_input,
            normalized_request=normalized,
            status=TaskStatus.ANALYZING,
            requested_outputs=outcome.required_outputs,
            constraints=cst,
            context=ctx,
        )
        self._tasks[tid] = task

        # Store clarifications if any required
        for clar in clarifications:
            self._clarifications[clar.clarification_id] = clar

        if clarifications:
            task.status = TaskStatus.WAITING_FOR_INPUT
            return TaskOrchestrationResult(
                task_id=tid,
                status=TaskStatus.WAITING_FOR_INPUT,
                required_outputs=outcome.required_outputs,
                clarifications=clarifications,
                blocking_issues=[],
                warnings=[],
            )

        # ── Step 3: Capability Resolution ─────────────────────────────────
        cap_reqs = self._cap_resolver.resolve_requirements(outcome)

        # ── Step 4: Task Decomposition into WorkUnits ─────────────────────
        task.status = TaskStatus.PLANNING
        work_units = self._decomposer.decompose(tid, outcome)

        # ── Step 5: Build & Validate TaskPlan ─────────────────────────────
        plan = self._planner.build_plan(task, outcome, work_units, version=1)
        self._plans[plan.plan_id] = plan
        task.current_plan_id = plan.plan_id

        # Determine Task Status from Plan readiness
        if plan.is_ready:
            task.status = TaskStatus.READY_FOR_EXECUTION
            task_status = TaskStatus.READY_FOR_EXECUTION
        else:
            task.status = TaskStatus.BLOCKED
            task_status = TaskStatus.BLOCKED

        return TaskOrchestrationResult(
            task_id=tid,
            plan_id=plan.plan_id,
            status=task_status,
            work_units=plan.work_units,
            dependencies=plan.dependencies,
            required_outputs=plan.expected_outputs,
            clarifications=[],
            blocking_issues=plan.blockers,
            warnings=plan.warnings,
        )

    def resolve_clarification(
        self, task_id: str, clarification_id: str, response_text: str
    ) -> TaskOrchestrationResult:
        """
        Resolves pending clarification and re-orchestrates task.
        """
        clar = self._clarifications.get(clarification_id)
        if not clar or clar.task_id != task_id:
            raise ValueError(f"Clarification '{clarification_id}' not found for task '{task_id}'")

        clar.user_response = response_text
        clar.status = ClarificationStatus.RESOLVED

        task = self._tasks.get(task_id)
        if not task:
            raise ValueError(f"Task '{task_id}' not found")

        # Combine original text with clarification response
        updated_input = f"{task.original_request}. Specifically: {response_text}"
        return self.orchestrate_task(
            user_input=updated_input,
            organization_id=task.organization_id,
            context=task.context,
            constraints=task.constraints,
            task_id=task_id,
        )

    def get_task(self, task_id: str) -> Optional[Task]:
        return self._tasks.get(task_id)

    def get_plan(self, plan_id: str) -> Optional[TaskPlan]:
        return self._plans.get(plan_id)
