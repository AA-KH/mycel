from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

from .models import SkillStatus, TeamSkillStatus, SkillImportance, SkillCategory

# ==========================================
# Skill Schemas
# ==========================================

class SkillCreate(BaseModel):
    skill_id: str = Field(..., pattern=r'^[a-z0-9_]+$')
    name: str
    display_name: str
    description: str
    domain: str
    category: SkillCategory
    status: SkillStatus = SkillStatus.ACTIVE
    metadata: Dict[str, Any] = Field(default_factory=dict)

class SkillUpdate(BaseModel):
    name: Optional[str] = None
    display_name: Optional[str] = None
    description: Optional[str] = None
    domain: Optional[str] = None
    category: Optional[SkillCategory] = None
    status: Optional[SkillStatus] = None
    metadata: Optional[Dict[str, Any]] = None

class SkillResponse(BaseModel):
    id: str
    skill_id: str
    name: str
    display_name: str
    description: str
    domain: str
    category: SkillCategory
    status: SkillStatus
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

# ==========================================
# Team Skill Assignment Schemas
# ==========================================

class TeamSkillAssignmentCreate(BaseModel):
    skill_id: str
    importance: SkillImportance = SkillImportance.SUPPORTING
    required: bool = False
    proficiency_baseline: int = Field(ge=0, le=100)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class TeamSkillAssignmentUpdate(BaseModel):
    importance: Optional[SkillImportance] = None
    required: Optional[bool] = None
    proficiency_baseline: Optional[int] = Field(None, ge=0, le=100)
    status: Optional[TeamSkillStatus] = None
    metadata: Optional[Dict[str, Any]] = None

class TeamSkillAssignmentResponse(BaseModel):
    id: str
    team_id: str
    skill_id: str
    importance: SkillImportance
    required: bool
    proficiency_baseline: int
    status: TeamSkillStatus
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
