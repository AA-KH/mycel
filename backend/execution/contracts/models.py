from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone


# ─────────────────────────────────────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────────────────────────────────────

class ContractStatus(str, Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    DEPRECATED = "DEPRECATED"
    ARCHIVED = "ARCHIVED"


class ContractReadiness(str, Enum):
    READY = "READY"
    READY_WITH_WARNINGS = "READY_WITH_WARNINGS"
    NOT_READY = "NOT_READY"


class ContractInputType(str, Enum):
    TEXT = "text"
    DOCUMENT = "document"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    URL = "url"
    JSON = "json"
    STRUCTURED_DATA = "structured_data"
    ARTIFACT_REFERENCE = "artifact_reference"


class ContractFailureCondition(str, Enum):
    INPUT_INVALID = "INPUT_INVALID"
    CAPABILITY_UNAVAILABLE = "CAPABILITY_UNAVAILABLE"
    PIPELINE_UNAVAILABLE = "PIPELINE_UNAVAILABLE"
    TOOL_UNAVAILABLE = "TOOL_UNAVAILABLE"
    EXECUTION_TIMEOUT = "EXECUTION_TIMEOUT"
    ARTIFACT_INVALID = "ARTIFACT_INVALID"
    QUALITY_FAILED = "QUALITY_FAILED"
    OUTPUT_MISSING = "OUTPUT_MISSING"
    HUMAN_APPROVAL_REQUIRED = "HUMAN_APPROVAL_REQUIRED"


# ─────────────────────────────────────────────────────────────────────────────
# Sub-models
# ─────────────────────────────────────────────────────────────────────────────

class ContractInputField(BaseModel):
    """Describes a single input field accepted by the contract."""
    input_id: str
    type: ContractInputType = ContractInputType.TEXT
    description: str = ""
    required: bool = True
    validation_rules: List[str] = Field(default_factory=list)


class ContractArtifactExpectation(BaseModel):
    """Describes an expected artifact that execution should produce."""
    artifact_type: str          # e.g. "video", "document", "code"
    required: bool = True
    format: Optional[str] = None  # e.g. "mp4", "pdf", "py"
    description: str = ""


class StageExpectation(BaseModel):
    """Lightweight expectation on a specific pipeline stage."""
    stage_id: str
    required: bool = True
    expected_input: Optional[str] = None
    expected_output: Optional[str] = None
    quality_requirement: Optional[str] = None   # quality_gate_id reference
    completion_condition: Optional[str] = None


class HandoffContract(BaseModel):
    """Defines what must be passed to the next system upon completion."""
    include_status: bool = True
    include_artifacts: bool = True
    include_outputs: bool = True
    include_quality_results: bool = True
    include_execution_summary: bool = True
    include_warnings: bool = True
    include_errors: bool = True
    notes: str = ""


class ExecutionContextReference(BaseModel):
    """
    Lightweight reference to what the Agent Runtime will need.
    Only IDs — not live objects.
    """
    task_id: Optional[str] = None
    team_id: str
    contract_id: str
    pipeline_id: str
    position_id: Optional[str] = None
    member_id: Optional[str] = None
    agent_id: Optional[str] = None


class ExecutionConstraints(BaseModel):
    """Declares constraints the runtime must honour. Not enforced here."""
    max_duration_seconds: Optional[int] = None
    max_tool_calls: Optional[int] = None
    allowed_tool_categories: List[str] = Field(default_factory=list)
    requires_human_approval: bool = False
    partial_output_allowed: bool = False
    allowed_output_types: List[str] = Field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
# Aggregate Root
# ─────────────────────────────────────────────────────────────────────────────

class TeamExecutionContract(BaseModel):
    """
    Formal agreement that governs how a Team accepts and completes
    a specific task type.

    This is a CONTRACT DEFINITION — not an execution engine.
    No LLM, no tool calls, no pipeline runs occur here.
    """

    # Identity
    contract_id: str                            # e.g. "creative.promotional_video.v1"
    team_id: str                                # must match an existing Team
    version: int = 1
    status: ContractStatus = ContractStatus.DRAFT
    description: str = ""

    # Task Acceptance
    accepted_task_types: List[str] = Field(default_factory=list)

    # Inputs
    required_inputs: List[ContractInputField] = Field(default_factory=list)
    optional_inputs: List[ContractInputField] = Field(default_factory=list)

    # Capability Requirements (IDs only — resolved via TeamCapabilityResolver)
    required_skills: List[str] = Field(default_factory=list)
    required_tools: List[str] = Field(default_factory=list)
    required_knowledge: List[str] = Field(default_factory=list)
    reasoning_profile: Optional[str] = None

    # Pipeline
    pipeline_id: str = ""                       # must belong to team_id
    stage_expectations: List[StageExpectation] = Field(default_factory=list)

    # Outputs
    output_contract_ids: List[str] = Field(default_factory=list)  # reference existing OutputContracts
    expected_artifacts: List[ContractArtifactExpectation] = Field(default_factory=list)

    # Quality (IDs only — executed by Quality System, not here)
    quality_gate_ids: List[str] = Field(default_factory=list)

    # Completion & Failure
    completion_criteria: List[str] = Field(default_factory=list)
    failure_conditions: List[ContractFailureCondition] = Field(default_factory=list)

    # Constraints
    execution_constraints: ExecutionConstraints = Field(default_factory=ExecutionConstraints)

    # Handoff
    handoff_contract: HandoffContract = Field(default_factory=HandoffContract)

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def is_active(self) -> bool:
        return self.status == ContractStatus.ACTIVE

    @property
    def is_executable_candidate(self) -> bool:
        """Only ACTIVE contracts are candidates for future runtime selection."""
        return self.status == ContractStatus.ACTIVE


# ─────────────────────────────────────────────────────────────────────────────
# Validation Result
# ─────────────────────────────────────────────────────────────────────────────

class ContractValidationIssue(BaseModel):
    code: str
    message: str
    severity: str   # "ERROR" | "WARNING"
    path: str
    source: str = "contract_validator"


class TeamContractValidationResult(BaseModel):
    contract_id: str
    team_id: str
    valid: bool = False
    readiness: ContractReadiness = ContractReadiness.NOT_READY
    errors: List[ContractValidationIssue] = Field(default_factory=list)
    warnings: List[ContractValidationIssue] = Field(default_factory=list)
    checks: int = 0
    validated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ContractValidationSummary(BaseModel):
    total_contracts: int = 0
    valid_contracts: int = 0
    invalid_contracts: int = 0
    ready_contracts: int = 0
    not_ready_contracts: int = 0
    total_errors: int = 0
    total_warnings: int = 0
    results: List[TeamContractValidationResult] = Field(default_factory=list)
