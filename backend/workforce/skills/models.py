from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

class SkillStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"

class TeamSkillStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"

class SkillImportance(str, Enum):
    CORE = "core"
    SUPPORTING = "supporting"
    OPTIONAL = "optional"

class SkillCategory(str, Enum):
    TECHNICAL = "technical"
    RESEARCH = "research"
    ANALYTICAL = "analytical"
    COMMUNICATION = "communication"
    LEGAL = "legal"
    BUSINESS = "business"
    OPERATIONAL = "operational"
    MANAGEMENT = "management"
    SECURITY = "security"
    QUALITY = "quality"
    OTHER = "other"

class Skill(BaseModel):
    """
    A reusable capability definition that can be referenced globally.
    """
    id: Optional[str] = None
    skill_id: str
    name: str
    display_name: str
    description: str
    domain: str
    category: SkillCategory
    status: SkillStatus = SkillStatus.ACTIVE
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TeamSkillAssignment(BaseModel):
    """
    Association between a Team and a expected Skill baseline.
    """
    id: Optional[str] = None
    team_id: str
    skill_id: str
    importance: SkillImportance = SkillImportance.SUPPORTING
    required: bool = False
    proficiency_baseline: int = Field(ge=0, le=100)
    status: TeamSkillStatus = TeamSkillStatus.ACTIVE
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
