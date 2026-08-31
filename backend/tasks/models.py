"""
Task Orchestration System Domain Models (Phase 10)

Defines explicit domain models for Task Orchestration:
- Task & TaskRequest
- TaskOutcome & TaskCapabilityRequirement
- WorkUnit & WorkUnitDependency
- TaskPlan, TaskPlanStatus, TaskClarification
- PlanBlocker, PlanWarning, TaskOrchestrationResult

Strict Boundaries:
- No execution state or live runtime state.
- No employee hiring assignments (positions only).
- No agent/tool execution credentials or secret data.
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone


# ─────────────────────────────────────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────────────────────────────────────

class TaskStatus(str, Enum):
    CREATED = "CREATED"
    ANALYZING = "ANALYZING"
    PLANNING = "PLANNING"
    PLAN_READY = "PLAN_READY"
    WAITING_FOR_INPUT = "WAITING_FOR_INPUT"
    BLOCKED = "BLOCKED"
    READY_FOR_EXECUTION = "READY_FOR_EXECUTION"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class TaskPriority(str, Enum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    URGENT = "URGENT"


class TaskPlanStatus(str, Enum):
    DRAFT = "DRAFT"
    VALIDATING = "VALIDATING"
    READY = "READY"
    SUPERSEDED = "SUPERSEDED"
    CANCELLED = "CANCELLED"
    INVALID = "INVALID"


class WorkUnitStatus(str, Enum):
    PENDING = "PENDING"
    READY = "READY"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    SKIPPED = "SKIPPED"


class DependencyType(str, Enum):
    OUTPUT_REQUIRED = "OUTPUT_REQUIRED"
    ARTIFACT_REQUIRED = "ARTIFACT_REQUIRED"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    QUALITY_REQUIRED = "QUALITY_REQUIRED"
    CONTRACT_REQUIRED = "CONTRACT_REQUIRED"


class BlockerCode(str, Enum):
    MISSING_OUTPUT = "MISSING_OUTPUT"
    NO_CAPABLE_TEAM = "NO_CAPABLE_TEAM"
    MISSING_PIPELINE = "MISSING_PIPELINE"
    MISSING_EXECUTION_CONTRACT = "MISSING_EXECUTION_CONTRACT"
    INVALID_EXECUTION_CONTRACT = "INVALID_EXECUTION_CONTRACT"
    INVALID_DEPENDENCY = "INVALID_DEPENDENCY"
    INVALID_EXECUTION_GRAPH = "INVALID_EXECUTION_GRAPH"
    MISSING_REQUIRED_INPUT = "MISSING_REQUIRED_INPUT"
    AMBIGUOUS_REQUEST = "AMBIGUOUS_REQUEST"
    COLLABORATION_CONTRACT_MISSING = "COLLABORATION_CONTRACT_MISSING"


class ClarificationStatus(str, Enum):
    PENDING = "PENDING"
    RESOLVED = "RESOLVED"
    EXPIRED = "EXPIRED"


class OutputModality(str, Enum):
    TEXT = "TEXT"
    IMAGE = "IMAGE"
    AUDIO = "AUDIO"
    VIDEO = "VIDEO"
    CODE = "CODE"
    WEBSITE = "WEBSITE"
    DOCUMENT = "DOCUMENT"
    SPREADSHEET = "SPREADSHEET"
    PRESENTATION = "PRESENTATION"
    DATA = "DATA"
    REPORT = "REPORT"


class ArtifactType(str, Enum):
    LOGO = "LOGO"
    POSTER = "POSTER"
    BANNER = "BANNER"
    SOCIAL_MEDIA_CREATIVE = "SOCIAL_MEDIA_CREATIVE"
    ILLUSTRATION = "ILLUSTRATION"
    VIDEO = "VIDEO"
    WEBSITE = "WEBSITE"
    LANDING_PAGE = "LANDING_PAGE"
    MARKETING_WEBSITE = "MARKETING_WEBSITE"
    PROMOTIONAL_WEBSITE = "PROMOTIONAL_WEBSITE"
    PITCH_DECK = "PITCH_DECK"
    RESEARCH_REPORT = "RESEARCH_REPORT"
    FINANCIAL_MODEL = "FINANCIAL_MODEL"
    FINANCIAL_FEASIBILITY_REPORT = "FINANCIAL_FEASIBILITY_REPORT"
    LEGAL_ASSESSMENT = "LEGAL_ASSESSMENT"
    FEASIBILITY_REPORT = "FEASIBILITY_REPORT"
    MARKET_RESEARCH_REPORT = "MARKET_RESEARCH_REPORT"
    CODE_BUNDLE = "CODE_BUNDLE"
    DOCUMENT = "DOCUMENT"


class PreviewType(str, Enum):
    IMAGE = "IMAGE"
    LIVE_WEBSITE = "LIVE_WEBSITE"
    SLIDE_VIEWER = "SLIDE_VIEWER"
    PDF_VIEWER = "PDF_VIEWER"
    VIDEO_PLAYER = "VIDEO_PLAYER"
    AUDIO_PLAYER = "AUDIO_PLAYER"
    DOCUMENT_VIEWER = "DOCUMENT_VIEWER"
    SPREADSHEET_VIEWER = "SPREADSHEET_VIEWER"
    CODE_VIEWER = "CODE_VIEWER"
    NONE = "NONE"


# ─────────────────────────────────────────────────────────────────────────────
# Context & Constraints
# ─────────────────────────────────────────────────────────────────────────────

class TaskContext(BaseModel):
    product_context: Optional[str] = None
    brand_context: Optional[str] = None
    target_audience: Optional[str] = None
    industry: Optional[str] = None
    jurisdiction: Optional[str] = None
    language: str = "en"
    user_constraints: List[str] = Field(default_factory=list)
    existing_artifacts: List[str] = Field(default_factory=list) # ArtifactReference IDs
    references: Dict[str, Any] = Field(default_factory=dict)


class TaskConstraints(BaseModel):
    deadline: Optional[datetime] = None
    budget: Optional[float] = None
    format: Optional[str] = None
    language: Optional[str] = None
    jurisdiction: Optional[str] = None
    brand_requirements: List[str] = Field(default_factory=list)
    platform: Optional[str] = None
    quality_level: str = "standard"


# ─────────────────────────────────────────────────────────────────────────────
# Task Request & Outcome
# ─────────────────────────────────────────────────────────────────────────────

class TaskRequest(BaseModel):
    request_id: str
    task_id: str
    user_input: str
    context: TaskContext = Field(default_factory=TaskContext)
    constraints: TaskConstraints = Field(default_factory=TaskConstraints)
    requested_outputs: List[str] = Field(default_factory=list)
    deadline: Optional[datetime] = None
    priority: TaskPriority = TaskPriority.NORMAL
    metadata: Dict[str, Any] = Field(default_factory=dict)


class OutputSpec(BaseModel):
    intent: str
    modality: OutputModality
    artifact_type: ArtifactType
    required_capabilities: List[str] = Field(default_factory=list)
    preview_type: PreviewType = PreviewType.NONE
    generation_required: bool = True

class TaskOutcome(BaseModel):
    objective: str
    intent: str = ""
    success_definition: str = ""
    required_outputs: List[str] = Field(default_factory=list)
    output_specs: List[OutputSpec] = Field(default_factory=list)
    constraints: TaskConstraints = Field(default_factory=TaskConstraints)


class TaskCapabilityRequirement(BaseModel):
    capability_id: str
    minimum_proficiency: str = "standard"
    required: bool = True
    source: str = "outcome"
    reason: str = ""


# ─────────────────────────────────────────────────────────────────────────────
# Work Unit & Dependency
# ─────────────────────────────────────────────────────────────────────────────

class WorkUnitDependency(BaseModel):
    dependency_id: str
    task_id: str
    from_work_unit_id: str
    to_work_unit_id: str
    dependency_type: DependencyType = DependencyType.OUTPUT_REQUIRED
    required: bool = True
    condition: Optional[str] = None
    description: str = ""


class WorkUnit(BaseModel):
    work_unit_id: str
    task_id: str
    team_id: str
    title: str
    objective: str
    inputs: List[str] = Field(default_factory=list)            # References/IDs only
    required_capabilities: List[str] = Field(default_factory=list)
    pipeline_id: Optional[str] = None
    execution_contract_id: Optional[str] = None
    collaboration_contract_id: Optional[str] = None
    expected_outputs: List[str] = Field(default_factory=list)   # Output Contract IDs
    quality_requirements: List[str] = Field(default_factory=list)# Quality gate IDs
    required_position: Optional[str] = None                    # Position ID (NOT employee)
    dependencies: List[str] = Field(default_factory=list)        # WorkUnit IDs this unit depends on
    constraints: Dict[str, Any] = Field(default_factory=dict)
    status: WorkUnitStatus = WorkUnitStatus.PENDING
    parallelizable: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ─────────────────────────────────────────────────────────────────────────────
# Blockers, Warnings, Clarifications
# ─────────────────────────────────────────────────────────────────────────────

class PlanBlocker(BaseModel):
    code: BlockerCode
    message: str
    work_unit_id: Optional[str] = None
    team_id: Optional[str] = None
    severity: str = "ERROR"


class PlanWarning(BaseModel):
    code: str
    message: str
    work_unit_id: Optional[str] = None
    severity: str = "WARNING"


class TaskClarification(BaseModel):
    clarification_id: str
    task_id: str
    question: str
    reason: str
    required: bool = True
    status: ClarificationStatus = ClarificationStatus.PENDING
    user_response: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ─────────────────────────────────────────────────────────────────────────────
# Task Plan & Orchestration Result
# ─────────────────────────────────────────────────────────────────────────────

class TaskPlan(BaseModel):
    plan_id: str
    task_id: str
    version: int = 1
    status: TaskPlanStatus = TaskPlanStatus.DRAFT
    objective: str
    work_units: List[WorkUnit] = Field(default_factory=list)
    dependencies: List[WorkUnitDependency] = Field(default_factory=list)
    expected_outputs: List[str] = Field(default_factory=list)
    completion_criteria: List[str] = Field(default_factory=list)
    failure_conditions: List[str] = Field(default_factory=list)
    blockers: List[PlanBlocker] = Field(default_factory=list)
    warnings: List[PlanWarning] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def is_ready(self) -> bool:
        return self.status == TaskPlanStatus.READY and len(self.blockers) == 0


class TaskOrchestrationResult(BaseModel):
    task_id: str
    plan_id: Optional[str] = None
    status: TaskStatus = TaskStatus.CREATED
    work_units: List[WorkUnit] = Field(default_factory=list)
    dependencies: List[WorkUnitDependency] = Field(default_factory=list)
    required_outputs: List[str] = Field(default_factory=list)
    clarifications: List[TaskClarification] = Field(default_factory=list)
    blocking_issues: List[PlanBlocker] = Field(default_factory=list)
    warnings: List[PlanWarning] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ─────────────────────────────────────────────────────────────────────────────
# Primary Task Entity
# ─────────────────────────────────────────────────────────────────────────────

class Task(BaseModel):
    task_id: str
    organization_id: str = "mycel_global"
    title: str
    description: str = ""
    original_request: str
    normalized_request: str = ""
    status: TaskStatus = TaskStatus.CREATED
    priority: TaskPriority = TaskPriority.NORMAL
    requested_outputs: List[str] = Field(default_factory=list)
    constraints: TaskConstraints = Field(default_factory=TaskConstraints)
    context: TaskContext = Field(default_factory=TaskContext)
    current_plan_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)
