"""
Autonomous Company — Domain Models (Phase 16)

This module defines all domain entities for the Autonomous Company control layer.

Architectural Invariants
------------------------
1.  Autonomy is a control layer.  Existing systems remain authoritative.
2.  Autonomy never bypasses permissions, grants itself privileges, or
    modifies its own policies.
3.  Every objective has explicit termination conditions.
4.  Every autonomous decision is recorded and auditable.
5.  Every plan is versioned; history is never overwritten.
6.  Quality Gates remain authoritative — task completion ≠ objective progress
    unless quality gates have passed.
7.  Hiring remains the authoritative selection authority.
8.  Agent creation is bounded per objective.
9.  Task creation is bounded per objective.
10. Kill switch stops all new autonomous actions immediately.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ─────────────────────────────────────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────────────────────────────────────

class ObjectiveStatus(str, Enum):
    DRAFT      = "DRAFT"
    ACTIVE     = "ACTIVE"
    PLANNING   = "PLANNING"
    EXECUTING  = "EXECUTING"
    EVALUATING = "EVALUATING"
    REPLANNING = "REPLANNING"
    BLOCKED    = "BLOCKED"
    PAUSED     = "PAUSED"
    COMPLETED  = "COMPLETED"
    FAILED     = "FAILED"
    CANCELLED  = "CANCELLED"
    EXPIRED    = "EXPIRED"


class ObjectivePriority(str, Enum):
    LOW      = "LOW"
    MEDIUM   = "MEDIUM"
    HIGH     = "HIGH"
    CRITICAL = "CRITICAL"


class AutonomyLevel(str, Enum):
    MANUAL     = "MANUAL"      # Human approves every action
    ASSISTED   = "ASSISTED"    # System proposes; human executes
    SUPERVISED = "SUPERVISED"  # Auto for low-risk; approval for high-risk
    AUTONOMOUS = "AUTONOMOUS"  # Auto within strict policy; approval for irreversible


class PlanStatus(str, Enum):
    DRAFT      = "DRAFT"
    VALIDATING = "VALIDATING"
    READY      = "READY"
    EXECUTING  = "EXECUTING"
    BLOCKED    = "BLOCKED"
    SUPERSEDED = "SUPERSEDED"
    COMPLETED  = "COMPLETED"
    FAILED     = "FAILED"


class MilestoneStatus(str, Enum):
    PENDING     = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED   = "COMPLETED"
    FAILED      = "FAILED"
    SKIPPED     = "SKIPPED"


class DecisionType(str, Enum):
    CREATE_TASK       = "CREATE_TASK"
    START_TASK        = "START_TASK"
    WAIT              = "WAIT"
    RETRY             = "RETRY"
    REPLAN            = "REPLAN"
    REQUEST_RESOURCE  = "REQUEST_RESOURCE"
    REQUEST_APPROVAL  = "REQUEST_APPROVAL"
    ESCALATE          = "ESCALATE"
    COMPLETE          = "COMPLETE"
    PAUSE             = "PAUSE"
    CANCEL            = "CANCEL"


class FailureType(str, Enum):
    TRANSIENT   = "TRANSIENT"    # Retry with backoff
    RESOURCE    = "RESOURCE"     # Employee/tool unavailable
    CAPABILITY  = "CAPABILITY"   # Required capability missing
    QUALITY     = "QUALITY"      # Quality gate failed
    DEPENDENCY  = "DEPENDENCY"   # Dependent task failed
    POLICY      = "POLICY"       # Policy violation
    TIMEOUT     = "TIMEOUT"      # Deadline exceeded
    SYSTEM      = "SYSTEM"       # Unexpected system error


class RiskLevel(str, Enum):
    LOW      = "LOW"
    MEDIUM   = "MEDIUM"
    HIGH     = "HIGH"
    CRITICAL = "CRITICAL"


class ActionCategory(str, Enum):
    READ_ONLY           = "READ_ONLY"
    REVERSIBLE          = "REVERSIBLE"
    IRREVERSIBLE        = "IRREVERSIBLE"
    EXTERNAL_SIDE_EFFECT = "EXTERNAL_SIDE_EFFECT"


class ActionStatus(str, Enum):
    PENDING   = "PENDING"
    APPROVED  = "APPROVED"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    REJECTED  = "REJECTED"
    EXPIRED   = "EXPIRED"


class AutonomyHealthStatus(str, Enum):
    HEALTHY  = "HEALTHY"
    DEGRADED = "DEGRADED"
    BLOCKED  = "BLOCKED"
    DISABLED = "DISABLED"


# ─────────────────────────────────────────────────────────────────────────────
# Success Criteria
# ─────────────────────────────────────────────────────────────────────────────

class SuccessCriteria(BaseModel):
    criterion_id: str = Field(
        default_factory=lambda: f"sc_{uuid.uuid4().hex[:8]}"
    )
    description: str
    verification_method: str = "artifact_exists"   # artifact_exists | quality_gate | evaluation | manual
    target_value: Optional[str] = None              # e.g. "performance_score > 80"
    met: bool = False
    verified_at: Optional[datetime] = None


# ─────────────────────────────────────────────────────────────────────────────
# Autonomy Budget
# ─────────────────────────────────────────────────────────────────────────────

class AutonomyBudget(BaseModel):
    """
    Per-objective budget that enforces all bounded-autonomy limits.
    None values mean 'no limit set' — policy_engine applies system defaults.
    """
    # Cost
    max_cost: Optional[float] = None
    spent_cost: float = 0.0

    # Iteration / loop protection
    max_iterations: int = 50
    current_iterations: int = 0
    max_replan_count: int = 5
    replan_count: int = 0

    # Task / Agent limits
    max_tasks: int = 30
    tasks_created: int = 0
    max_agents: int = 10
    agents_created: int = 0

    # Per-task retry
    max_retries_per_task: int = 3

    # Alert thresholds
    budget_alert_threshold: float = 0.80   # warn at 80% of max_cost

    @property
    def cost_exhausted(self) -> bool:
        return self.max_cost is not None and self.spent_cost >= self.max_cost

    @property
    def iterations_exhausted(self) -> bool:
        return self.current_iterations >= self.max_iterations

    @property
    def tasks_exhausted(self) -> bool:
        return self.tasks_created >= self.max_tasks

    @property
    def replans_exhausted(self) -> bool:
        return self.replan_count >= self.max_replan_count

    @property
    def cost_alert(self) -> bool:
        if self.max_cost is None:
            return False
        return (self.spent_cost / self.max_cost) >= self.budget_alert_threshold


# ─────────────────────────────────────────────────────────────────────────────
# Objective Constraints
# ─────────────────────────────────────────────────────────────────────────────

class ObjectiveConstraints(BaseModel):
    deadline: Optional[datetime] = None
    language: str = "en"
    jurisdiction: Optional[str] = None
    quality_level: str = "standard"
    brand_requirements: List[str] = Field(default_factory=list)
    platform: Optional[str] = None
    extra: Dict[str, Any] = Field(default_factory=dict)


# ─────────────────────────────────────────────────────────────────────────────
# Company Objective
# ─────────────────────────────────────────────────────────────────────────────

class CompanyObjective(BaseModel):
    """
    A company-level objective the Autonomous Company pursues.
    This is the primary entity owned by Phase 16.
    """
    objective_id: str = Field(
        default_factory=lambda: f"obj_{uuid.uuid4().hex[:10]}"
    )
    organization_id: str

    title: str
    description: str
    priority: ObjectivePriority = ObjectivePriority.MEDIUM
    status: ObjectiveStatus = ObjectiveStatus.DRAFT
    autonomy_level: AutonomyLevel = AutonomyLevel.SUPERVISED

    # What 'done' looks like
    success_criteria: List[SuccessCriteria] = Field(default_factory=list)
    constraints: ObjectiveConstraints = Field(default_factory=ObjectiveConstraints)
    budget_config: AutonomyBudget = Field(default_factory=AutonomyBudget)

    # Plan version history — ALL plan IDs, oldest first; never deleted
    plan_ids: List[str] = Field(default_factory=list)
    current_plan_id: Optional[str] = None

    # Loop protection counters
    iteration_count: int = 0

    # Ownership
    created_by: str = "system"

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    completed_at: Optional[datetime] = None


# ─────────────────────────────────────────────────────────────────────────────
# Milestone
# ─────────────────────────────────────────────────────────────────────────────

class Milestone(BaseModel):
    milestone_id: str = Field(
        default_factory=lambda: f"ms_{uuid.uuid4().hex[:8]}"
    )
    objective_id: str
    title: str
    description: str = ""
    sequence: int = 0                  # Ordering within plan
    status: MilestoneStatus = MilestoneStatus.PENDING

    # Constituent task references (Task.task_id values)
    task_ids: List[str] = Field(default_factory=list)

    # Success criteria specific to this milestone
    success_criteria: List[SuccessCriteria] = Field(default_factory=list)

    # Required output types for milestone completion
    required_outputs: List[str] = Field(default_factory=list)

    completed_at: Optional[datetime] = None


# ─────────────────────────────────────────────────────────────────────────────
# Task Request Descriptor (not the actual Task)
# ─────────────────────────────────────────────────────────────────────────────

class TaskRequestDescriptor(BaseModel):
    """
    Describes a task the plan wants created.
    The actual TaskRequest is built and submitted to TaskOrchestrator by
    AutonomousActionExecutor — never by the planner itself.
    """
    descriptor_id: str = Field(
        default_factory=lambda: f"trd_{uuid.uuid4().hex[:8]}"
    )
    milestone_id: str
    title: str
    description: str
    required_capabilities: List[str] = Field(default_factory=list)
    required_outputs: List[str] = Field(default_factory=list)
    preferred_team_id: Optional[str] = None
    priority: str = "NORMAL"
    estimated_cost: Optional[float] = None
    depends_on: List[str] = Field(
        default_factory=list,
        description="List of descriptor_ids that must complete first"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Company Plan
# ─────────────────────────────────────────────────────────────────────────────

class CompanyPlan(BaseModel):
    """
    A versioned execution plan for a CompanyObjective.
    Each replan creates a new version; old versions are preserved.
    """
    plan_id: str = Field(
        default_factory=lambda: f"plan_{uuid.uuid4().hex[:10]}"
    )
    objective_id: str
    version: int = 1
    status: PlanStatus = PlanStatus.DRAFT

    milestones: List[Milestone] = Field(default_factory=list)
    task_descriptors: List[TaskRequestDescriptor] = Field(default_factory=list)

    # Lightweight dependency graph: descriptor_id → [dependent_descriptor_ids]
    dependency_graph: Dict[str, List[str]] = Field(default_factory=dict)

    # Critical path: ordered list of descriptor_ids on longest dependency chain
    critical_path: List[str] = Field(default_factory=list)

    # Required capabilities at objective level
    required_capabilities: List[str] = Field(default_factory=list)

    estimated_cost: Optional[float] = None
    validation_blockers: List[str] = Field(default_factory=list)
    validation_warnings: List[str] = Field(default_factory=list)

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


# ─────────────────────────────────────────────────────────────────────────────
# Autonomy Decision
# ─────────────────────────────────────────────────────────────────────────────

class AutonomyDecision(BaseModel):
    """
    A recorded autonomous decision. Every decision must have a reason and
    evidence — no black-box autonomy.
    """
    decision_id: str = Field(
        default_factory=lambda: f"dec_{uuid.uuid4().hex[:10]}"
    )
    objective_id: str
    plan_version: int = 0

    decision_type: DecisionType
    reason: str
    evidence: Dict[str, Any] = Field(default_factory=dict)
    trigger: str = ""         # e.g. "TASK_COMPLETED", "TASK_FAILED", "SCHEDULED"

    risk_level: RiskLevel = RiskLevel.LOW
    requires_approval: bool = False
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None

    # Reference to the task/plan being acted on (if applicable)
    target_descriptor_id: Optional[str] = None
    target_task_id: Optional[str] = None

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


# ─────────────────────────────────────────────────────────────────────────────
# Autonomous Action
# ─────────────────────────────────────────────────────────────────────────────

class AutonomousAction(BaseModel):
    """
    The execution record of a single autonomous action, created after a
    decision is made and approved (if required).
    """
    action_id: str = Field(
        default_factory=lambda: f"act_{uuid.uuid4().hex[:10]}"
    )
    objective_id: str
    decision_id: str

    action_type: DecisionType
    action_category: ActionCategory = ActionCategory.REVERSIBLE
    risk_level: RiskLevel = RiskLevel.LOW

    status: ActionStatus = ActionStatus.PENDING

    # Human-readable summary for audit log
    description: str = ""

    # Reference to the system entity created/affected by this action
    result_reference: Optional[str] = None   # e.g. task_id, plan_id

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    completed_at: Optional[datetime] = None


# ─────────────────────────────────────────────────────────────────────────────
# Escalation
# ─────────────────────────────────────────────────────────────────────────────

class AutonomyEscalation(BaseModel):
    """
    Created when the autonomy engine cannot make forward progress and
    requires human intervention.  Contains a complete context package
    so the human does not need to read raw logs.
    """
    escalation_id: str = Field(
        default_factory=lambda: f"esc_{uuid.uuid4().hex[:8]}"
    )
    objective_id: str
    reason: str
    current_state_summary: str
    attempts_made: int = 0
    failed_strategies: List[str] = Field(default_factory=list)
    recommended_options: List[str] = Field(default_factory=list)

    resolved_at: Optional[datetime] = None
    resolution: Optional[str] = None

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


# ─────────────────────────────────────────────────────────────────────────────
# Company State Snapshot
# ─────────────────────────────────────────────────────────────────────────────

class MilestoneProgress(BaseModel):
    milestone_id: str
    title: str
    status: MilestoneStatus
    total_tasks: int = 0
    completed_tasks: int = 0   # Only tasks that passed quality gates
    failed_tasks: int = 0
    progress_pct: float = 0.0  # 0.0 – 1.0


class CompanyStateSnapshot(BaseModel):
    """
    Derived state snapshot — NOT the source of truth.
    Hiring, Task, Agent, Evaluation systems remain authoritative.
    """
    objective_id: str
    plan_version: int = 0

    # Task counts
    active_task_count: int = 0
    completed_task_count: int = 0   # Passed quality gate
    failed_task_count: int = 0
    blocked_task_count: int = 0

    # Milestone-level rollup
    milestone_progress: List[MilestoneProgress] = Field(default_factory=list)

    # Overall progress: 0.0 – 1.0 (weighted milestone completion)
    overall_progress: float = 0.0

    # Summaries (not raw system data)
    quality_state: Dict[str, Any] = Field(default_factory=dict)
    budget_state: Dict[str, Any] = Field(default_factory=dict)
    resource_utilization: Dict[str, Any] = Field(default_factory=dict)

    # Any active blockers or escalations
    active_blockers: List[str] = Field(default_factory=list)
    has_escalation: bool = False

    last_evaluated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


# ─────────────────────────────────────────────────────────────────────────────
# Autonomy Policy
# ─────────────────────────────────────────────────────────────────────────────

class AutonomyPolicy(BaseModel):
    """
    Per-organization or per-objective policy constraints.
    The autonomy engine READS these; it cannot modify them.
    """
    # Action permissions
    allow_irreversible_actions: bool = False
    allow_external_side_effects: bool = False

    # Concurrency
    max_concurrent_agents: int = 5
    max_concurrent_tasks: int = 10

    # Approval threshold: actions at or above this risk level require approval
    require_approval_threshold: RiskLevel = RiskLevel.HIGH

    # Budget alerts
    budget_alert_threshold: float = 0.80

    # Kill switch (globally set — autonomy reads, cannot write)
    kill_switch_active: bool = False


# ─────────────────────────────────────────────────────────────────────────────
# Approval Gate Result
# ─────────────────────────────────────────────────────────────────────────────

class ApprovalResult(BaseModel):
    required: bool
    reason: str
    gate_name: str = ""
    risk_level: RiskLevel = RiskLevel.LOW


# ─────────────────────────────────────────────────────────────────────────────
# Plan Validation Result
# ─────────────────────────────────────────────────────────────────────────────

class PlanValidationResult(BaseModel):
    valid: bool
    blockers: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
# Completion Validation Result
# ─────────────────────────────────────────────────────────────────────────────

class CompletionValidationResult(BaseModel):
    complete: bool
    missing: List[str] = Field(default_factory=list)
    unmet_criteria: List[str] = Field(default_factory=list)
    reason: str = ""


# ─────────────────────────────────────────────────────────────────────────────
# Failure Analysis Result
# ─────────────────────────────────────────────────────────────────────────────

class FailureAnalysisResult(BaseModel):
    failure_type: FailureType
    recoverable: bool
    recommendation: str          # RETRY | REPLAN | ESCALATE | FAIL
    reason: str
    loop_detected: bool = False


# ─────────────────────────────────────────────────────────────────────────────
# Autonomy Health
# ─────────────────────────────────────────────────────────────────────────────

class AutonomyHealth(BaseModel):
    status: AutonomyHealthStatus = AutonomyHealthStatus.HEALTHY
    active_objectives: int = 0
    kill_switch_active: bool = False
    blocked_objectives: int = 0
    escalations_pending: int = 0
    message: str = "System operational"
    checked_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
