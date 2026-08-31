"""
Team Collaboration Contract — Data Models (TOS 19)

These models define how one Team formally requests and receives work
from another Team. They are CONTRACT DEFINITIONS only.

No execution occurs here:
    ✗ No LLM calls
    ✗ No pipeline execution
    ✗ No tool invocation
    ✗ No agent creation
    ✗ No artifact generation
    ✗ No hiring
    ✗ No task routing
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone

# Reuse the shared input field types from TOS 18 contracts
from execution.contracts.models import ContractInputField, ContractInputType


# ─────────────────────────────────────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────────────────────────────────────

class CollaborationStatus(str, Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    DEPRECATED = "DEPRECATED"
    ARCHIVED = "ARCHIVED"


class CollaborationReadiness(str, Enum):
    READY = "READY"
    READY_WITH_WARNINGS = "READY_WITH_WARNINGS"
    NOT_READY = "NOT_READY"


class CollaborationSequenceType(str, Enum):
    """How this collaboration relates to other collaborations in a future task graph."""
    SEQUENTIAL = "SEQUENTIAL"    # providing team must complete before requesting team proceeds
    PARALLEL = "PARALLEL"        # providing team and requesting team may work concurrently
    CONDITIONAL = "CONDITIONAL"  # collaboration only occurs if a declared condition is met


class CollaborationHandoffStatus(str, Enum):
    """Expected status codes in a collaboration handoff result."""
    READY = "READY"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    PARTIAL = "PARTIAL"


class CollaborationDependencyType(str, Enum):
    REQUIRED_INPUT = "required_input"
    REQUIRED_ARTIFACT = "required_artifact"
    REQUIRED_APPROVAL = "required_approval"
    REQUIRED_QUALITY_RESULT = "required_quality_result"
    REQUIRED_PREVIOUS_TEAM_OUTPUT = "required_previous_team_output"


class CollaborationFailureCondition(str, Enum):
    INPUT_INVALID = "INPUT_INVALID"
    CAPABILITY_UNAVAILABLE = "CAPABILITY_UNAVAILABLE"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    PIPELINE_UNAVAILABLE = "PIPELINE_UNAVAILABLE"
    OUTPUT_MISSING = "OUTPUT_MISSING"
    QUALITY_FAILED = "QUALITY_FAILED"
    ARTIFACT_INVALID = "ARTIFACT_INVALID"
    DEPENDENCY_FAILED = "DEPENDENCY_FAILED"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    TIMEOUT = "TIMEOUT"


# ─────────────────────────────────────────────────────────────────────────────
# Sub-models
# ─────────────────────────────────────────────────────────────────────────────

class CollaborationDependency(BaseModel):
    """
    Represents a dependency this collaboration has on another contract or output.
    No dependency resolution engine is implemented — this is a declaration only.
    """
    dependency_id: str
    depends_on_contract: str          # contract_id of the upstream contract
    required_status: CollaborationHandoffStatus = CollaborationHandoffStatus.COMPLETED
    dependency_type: CollaborationDependencyType = CollaborationDependencyType.REQUIRED_PREVIOUS_TEAM_OUTPUT
    description: str = ""


class CollaborationConstraints(BaseModel):
    """
    Declares runtime constraints for future execution infrastructure.
    This contract does NOT enforce these — the Agent Runtime does.
    """
    max_round_trips: int = 1          # 1 = single request→response, 2 = with clarification
    requires_human_approval: bool = False
    requires_quality_pass: bool = True
    allowed_output_types: List[str] = Field(default_factory=list)
    timeout_seconds: Optional[int] = None
    partial_output_allowed: bool = False


class CollaborationHandoffContract(BaseModel):
    """
    Defines what the providing Team must hand back to the requesting Team.
    Transport is NOT implemented here.
    """
    include_status: bool = True
    include_artifacts: bool = True       # ArtifactReferences, not raw binaries
    include_outputs: bool = True
    include_quality_results: bool = True
    include_source_references: bool = False
    include_execution_summary: bool = True
    include_warnings: bool = True
    include_errors: bool = True
    notes: str = ""


# ─────────────────────────────────────────────────────────────────────────────
# Aggregate Root
# ─────────────────────────────────────────────────────────────────────────────

class TeamCollaborationContract(BaseModel):
    """
    Formal agreement governing how one Team requests and receives work from another.

    Key invariants:
        - requesting_team_id != providing_team_id  (no self-collaboration by default)
        - Both teams must exist in TeamRegistry
        - Providing team must satisfy required_capabilities via TeamCapabilityResolver
        - If execution_contract_id is set, it must belong to the providing team
        - If pipeline_id is set, it must belong to the providing team
        - ACTIVE contracts are immutable — create a new version to change

    This is a CONTRACT DEFINITION. Nothing is executed here.
    """

    # Identity
    contract_id: str                        # e.g. "research_to_developer.requirements.v1"
    version: int = 1
    status: CollaborationStatus = CollaborationStatus.DRAFT
    purpose: str = ""

    # Team Roles
    requesting_team_id: str                 # the team that requests the work
    providing_team_id: str                  # the team that performs the work

    # Request Classification
    request_type: str                       # e.g. "research_report", "compliance_review"
    accepted_request_types: List[str] = Field(default_factory=list)

    # Inputs flowing FROM requesting team TO providing team
    required_inputs: List[ContractInputField] = Field(default_factory=list)
    optional_inputs: List[ContractInputField] = Field(default_factory=list)

    # Capabilities the providing team must satisfy (IDs, not objects)
    required_capabilities: List[str] = Field(default_factory=list)
    required_tools: List[str] = Field(default_factory=list)
    required_knowledge: List[str] = Field(default_factory=list)
    required_reasoning: Optional[str] = None

    # Execution Contract & Pipeline (providing team)
    execution_contract_id: Optional[str] = None    # must belong to providing_team_id
    pipeline_id: Optional[str] = None              # must belong to providing_team_id

    # Outputs flowing FROM providing team TO requesting team
    required_output_contract_ids: List[str] = Field(default_factory=list)

    # Quality requirements (executed by Quality System, declared here)
    quality_gate_ids: List[str] = Field(default_factory=list)

    # Sequencing & Dependencies
    sequence_type: CollaborationSequenceType = CollaborationSequenceType.SEQUENTIAL
    condition: Optional[str] = None         # for CONDITIONAL: plain English condition description
    dependencies: List[CollaborationDependency] = Field(default_factory=list)

    # Completion & Failure
    completion_criteria: List[str] = Field(default_factory=list)
    failure_conditions: List[CollaborationFailureCondition] = Field(default_factory=list)

    # Constraints & Handoff
    collaboration_constraints: CollaborationConstraints = Field(
        default_factory=CollaborationConstraints
    )
    handoff_contract: CollaborationHandoffContract = Field(
        default_factory=CollaborationHandoffContract
    )

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def is_active(self) -> bool:
        return self.status == CollaborationStatus.ACTIVE

    @property
    def is_usable_candidate(self) -> bool:
        """Only ACTIVE contracts are candidates for future execution systems."""
        return self.status == CollaborationStatus.ACTIVE


# ─────────────────────────────────────────────────────────────────────────────
# Validation Result Models
# ─────────────────────────────────────────────────────────────────────────────

class CollaborationValidationIssue(BaseModel):
    code: str
    message: str
    severity: str           # "ERROR" | "WARNING"
    path: str
    source: str = "collaboration_validator"


class TeamCollaborationValidationResult(BaseModel):
    contract_id: str
    requesting_team_id: str
    providing_team_id: str
    valid: bool = False
    readiness: CollaborationReadiness = CollaborationReadiness.NOT_READY
    errors: List[CollaborationValidationIssue] = Field(default_factory=list)
    warnings: List[CollaborationValidationIssue] = Field(default_factory=list)
    checks: int = 0
    validated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CollaborationValidationSummary(BaseModel):
    total_contracts: int = 0
    valid_contracts: int = 0
    invalid_contracts: int = 0
    ready_contracts: int = 0
    not_ready_contracts: int = 0
    total_errors: int = 0
    total_warnings: int = 0
    results: List[TeamCollaborationValidationResult] = Field(default_factory=list)
