from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from enum import Enum

class PositionStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"

class PositionType(str, Enum):
    INDIVIDUAL_CONTRIBUTOR = "individual_contributor"
    LEADERSHIP = "leadership"
    REVIEWER = "reviewer"
    SPECIALIST = "specialist"
    GENERALIST = "generalist"

class Seniority(str, Enum):
    INTERN = "intern"
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    PRINCIPAL = "principal"

class Criticality(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class Requiredness(str, Enum):
    REQUIRED = "required"
    OPTIONAL = "optional"

# ---------------------------------------------------------
# Position Requirements
# ---------------------------------------------------------
class PositionSkillRequirement(BaseModel):
    skill_id: str
    minimum_proficiency: int = 50
    required: bool = True
    importance: str = "medium"

class PositionToolRequirement(BaseModel):
    tool_id: str
    required: bool = True

class PositionKnowledgeRequirement(BaseModel):
    knowledge_space_id: str
    required: bool = True

class PositionReasoningRequirement(BaseModel):
    preferred_strategy_id: str
    required: bool = False

# ---------------------------------------------------------
# Workforce Settings
# ---------------------------------------------------------
class WorkforceRequirement(BaseModel):
    min_headcount: int = 0
    max_headcount: Optional[int] = None
    recommended_headcount: int = 1
    requiredness: Requiredness = Requiredness.REQUIRED

# ---------------------------------------------------------
# Position Identity
# ---------------------------------------------------------
class Position(BaseModel):
    id: Optional[str] = None
    position_id: str
    team_id: str
    
    name: str
    display_name: str
    description: str = ""
    purpose: str = ""
    
    version: str = "1.0.0"
    status: PositionStatus = PositionStatus.DRAFT
    
    position_type: PositionType = PositionType.INDIVIDUAL_CONTRIBUTOR
    seniority: Seniority = Seniority.MID
    criticality: Criticality = Criticality.MEDIUM
    
    responsibilities: List[str] = Field(default_factory=list)
    workforce: WorkforceRequirement = Field(default_factory=WorkforceRequirement)
    
    # Requirements
    required_skills: List[PositionSkillRequirement] = Field(default_factory=list)
    required_tools: List[PositionToolRequirement] = Field(default_factory=list)
    required_knowledge: List[PositionKnowledgeRequirement] = Field(default_factory=list)
    reasoning_requirements: List[PositionReasoningRequirement] = Field(default_factory=list)
    
    # Pipeline & Operational Responsibilities
    pipeline_responsibilities: List[str] = Field(default_factory=list) # pipeline_ids
    stage_responsibilities: List[str] = Field(default_factory=list) # stage_definition_ids
    output_responsibilities: List[str] = Field(default_factory=list) # output_contract_ids
    quality_responsibilities: List[str] = Field(default_factory=list) # quality_gate_ids
    
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# ---------------------------------------------------------
# Effective Capability Profile
# ---------------------------------------------------------
class EffectivePositionCapabilityProfile(BaseModel):
    position_id: str
    team_id: str
    
    skills: List[PositionSkillRequirement]
    tools: List[PositionToolRequirement]
    knowledge: List[PositionKnowledgeRequirement]
    reasoning: List[PositionReasoningRequirement]
    
    pipeline_responsibilities: List[str]
    stage_responsibilities: List[str]
    output_responsibilities: List[str]
    quality_responsibilities: List[str]
