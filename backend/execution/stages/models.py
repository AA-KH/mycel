from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from enum import Enum

class StageDefinitionStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"

class StageCategory(str, Enum):
    RESEARCH = "research"
    ANALYSIS = "analysis"
    PLANNING = "planning"
    RETRIEVAL = "retrieval"
    GENERATION = "generation"
    TRANSFORMATION = "transformation"
    CODING = "coding"
    TESTING = "testing"
    VERIFICATION = "verification"
    REVIEW = "review"
    COMMUNICATION = "communication"
    CREATIVE = "creative"
    LEGAL = "legal"
    OUTPUT = "output"

# ---------------------------------------------------------
# Contracts
# ---------------------------------------------------------
class StageInputContract(BaseModel):
    input_type: str
    required_fields: List[str] = Field(default_factory=list)
    optional_fields: List[str] = Field(default_factory=list)
    description: str = ""


    quantity: int = 1
    format: str = "any"
    schema_ref: Optional[str] = None
    artifact_required: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)

class StageValidationContract(BaseModel):
    required_outputs: List[str] = Field(default_factory=list)
    required_artifacts: bool = False
    citation_required: bool = False
    verification_required: bool = False
    minimum_quality_conditions: List[str] = Field(default_factory=list)

# ---------------------------------------------------------
# Requirement Contracts (The core for Smart Hiring)
# ---------------------------------------------------------
class StageSkillRequirement(BaseModel):
    skill_id: str
    minimum_proficiency: int = 50
    required: bool = True
    importance: int = 1

class StageToolRequirement(BaseModel):
    tool_id: str
    required: bool = True
    access_mode: str = "read_write"
    importance: int = 1

class KnowledgeRequirementType(str, Enum):
    NO_KNOWLEDGE = "no_knowledge"
    OPTIONAL_KNOWLEDGE = "optional_knowledge"
    REQUIRED_KNOWLEDGE = "required_knowledge"

class StageKnowledgeRequirement(BaseModel):
    requirement_type: KnowledgeRequirementType = KnowledgeRequirementType.NO_KNOWLEDGE
    domain: Optional[str] = None
    source_trust: Optional[str] = None
    jurisdiction: Optional[str] = None
    freshness_requirement: Optional[str] = None

class StageReasoningRequirement(BaseModel):
    reasoning_strategy_id: Optional[str] = None
    required: bool = True

class StageRequirementContract(BaseModel):
    skills: List[StageSkillRequirement] = Field(default_factory=list)
    tools: List[StageToolRequirement] = Field(default_factory=list)
    knowledge: StageKnowledgeRequirement = Field(default_factory=StageKnowledgeRequirement)
    reasoning: StageReasoningRequirement = Field(default_factory=StageReasoningRequirement)
    output_contract_id: Optional[str] = None

# ---------------------------------------------------------
# Policies & Conditions
# ---------------------------------------------------------
class StageFailurePolicy(BaseModel):
    retryable: bool = False
    max_attempts: int = 1
    fail_pipeline: bool = True

class StagePrecondition(BaseModel):
    requires: str

class StagePostcondition(BaseModel):
    ensures: str

# ---------------------------------------------------------
# Stage Definition Aggregate Root
# ---------------------------------------------------------
class StageDefinition(BaseModel):
    """
    Defines WHAT a stage actually represents.
    This is a reusable capability specification, NOT a node in a specific pipeline.
    """
    id: Optional[str] = None
    stage_definition_id: str
    name: str
    display_name: str
    description: str = ""
    purpose: str
    domain: str = "global"
    category: StageCategory
    version: str = "1.0.0"
    status: StageDefinitionStatus = StageDefinitionStatus.DRAFT
    
    input_contract: StageInputContract
    requirement_contract: StageRequirementContract
    validation_contract: StageValidationContract = Field(default_factory=StageValidationContract)
    failure_policy: StageFailurePolicy = Field(default_factory=StageFailurePolicy)
    
    preconditions: List[StagePrecondition] = Field(default_factory=list)
    postconditions: List[StagePostcondition] = Field(default_factory=list)
    
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
