from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from enum import Enum

class ReasoningProfileStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"

# ---------------------------------------------------------
# Policies
# ---------------------------------------------------------
class EvidencePolicy(BaseModel):
    prefer_primary_sources: bool = True
    citation_required: bool = False
    source_cross_validation: bool = False
    minimum_sources: int = 1

class VerificationPolicy(BaseModel):
    verify_important_claims: bool = True
    code_execution_required: bool = False
    manager_review_required: bool = False

class UncertaintyPolicy(BaseModel):
    admit_unknowns: bool = True
    request_more_information: bool = False
    flag_conflicting_evidence: bool = True

class QualityPolicy(BaseModel):
    accuracy_focus: bool = True
    brand_consistency: bool = False
    technical_correctness: bool = True

class OutputPolicy(BaseModel):
    structured_summary: bool = True
    include_confidence_notes: bool = False
    include_risk_notes: bool = False

class ReasoningPolicies(BaseModel):
    evidence: EvidencePolicy = Field(default_factory=EvidencePolicy)
    verification: VerificationPolicy = Field(default_factory=VerificationPolicy)
    uncertainty: UncertaintyPolicy = Field(default_factory=UncertaintyPolicy)
    quality: QualityPolicy = Field(default_factory=QualityPolicy)
    output: OutputPolicy = Field(default_factory=OutputPolicy)


# ---------------------------------------------------------
# Core Domain Models
# ---------------------------------------------------------
class TeamReasoningProfile(BaseModel):
    """
    Defines the high-level reasoning methodology for a specific Team.
    """
    id: Optional[str] = None
    team_id: str
    name: str
    display_name: str
    description: str
    version: str = "1.0.0"
    status: ReasoningProfileStatus = ReasoningProfileStatus.ACTIVE
    
    principles: List[str] = Field(default_factory=list)
    policies: ReasoningPolicies = Field(default_factory=ReasoningPolicies)
    
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TeamReasoningStrategyAssignment(BaseModel):
    """
    Maps a TeamReasoningProfile to a concrete ReasoningStrategy (e.g. `research_verify`).
    """
    id: Optional[str] = None
    reasoning_profile_id: str
    strategy_id: str
    priority: int = 0
    required: bool = False
    conditions: Dict[str, Any] = Field(default_factory=dict)
    status: str = "active"
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
