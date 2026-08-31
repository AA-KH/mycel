from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone

class CapabilityType(str, Enum):
    SKILL = "skill"
    TOOL = "tool"
    KNOWLEDGE = "knowledge"
    REASONING = "reasoning"
    PIPELINE = "pipeline"
    STAGE = "stage"
    OUTPUT = "output"
    QUALITY = "quality"

class CapabilityStatus(str, Enum):
    REQUIRED = "required"
    OPTIONAL = "optional"
    DENIED = "denied"
    INACTIVE = "inactive"

class CapabilitySourceType(str, Enum):
    TEAM_COMMON = "team_common"
    POSITION = "position"
    MEMBER = "member"
    SPECIALIZATION = "specialization"
    SYSTEM = "system"

class CapabilityProvenance(BaseModel):
    capability_id: str
    capability_type: CapabilityType
    source_type: CapabilitySourceType
    source_id: str
    inherited_from: Optional[str] = None
    priority: int = 0
    reason: Optional[str] = None

class ResolvedCapability(BaseModel):
    capability_id: str
    capability_type: CapabilityType
    name: str
    source_type: CapabilitySourceType
    source_id: str
    proficiency: Optional[int] = None
    status: CapabilityStatus = CapabilityStatus.OPTIONAL
    provenance: CapabilityProvenance
    constraints: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class CapabilityConflict(BaseModel):
    capability_id: str
    conflict_type: str
    message: str

class CapabilityGapType(str, Enum):
    MISSING = "missing"
    INSUFFICIENT_PROFICIENCY = "insufficient_proficiency"
    DENIED = "denied"
    INACTIVE = "inactive"
    INCOMPATIBLE = "incompatible"

class CapabilityGap(BaseModel):
    capability_id: str
    gap_type: CapabilityGapType
    required_proficiency: Optional[int] = None
    actual_proficiency: Optional[int] = None
    message: str

class CapabilitySnapshot(BaseModel):
    snapshot_id: str
    subject_type: str
    subject_id: str
    subject_version: str
    resolved_capabilities: List[ResolvedCapability]
    resolution_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    resolver_version: str = "1.0.0"
    hash: str

class CapabilityResolutionResult(BaseModel):
    subject_id: str
    subject_type: str
    capabilities: List[ResolvedCapability]
    provenance: List[CapabilityProvenance]
    conflicts: List[CapabilityConflict] = Field(default_factory=list)
    gaps: List[CapabilityGap] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    resolved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
