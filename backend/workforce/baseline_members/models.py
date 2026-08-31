from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class BaselineStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"

class BaselineSkillProficiency(BaseModel):
    level: int = Field(ge=0, le=100)

class BaselineMember(BaseModel):
    """
    The canonical template for a Team Position.
    Represents the minimum expected worker before individual specialization.
    """
    baseline_member_id: str
    team_id: str
    position_id: str
    
    display_name: str
    description: str
    
    status: BaselineStatus = BaselineStatus.ACTIVE
    baseline_version: str = "1.0.0"
    
    skills: Dict[str, BaselineSkillProficiency] = Field(default_factory=dict)
    tools: List[str] = Field(default_factory=list)
    knowledge: List[str] = Field(default_factory=list)
    
    reasoning_profile: Optional[str] = None
    
    pipeline_responsibilities: List[str] = Field(default_factory=list)
    stage_responsibilities: List[str] = Field(default_factory=list)
    output_responsibilities: List[str] = Field(default_factory=list)
    quality_responsibilities: List[str] = Field(default_factory=list)
    
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
