from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

from .team_models import TeamToolStatus, ToolImportance, AccessMode

class TeamToolAssignmentCreate(BaseModel):
    tool_id: str
    importance: ToolImportance = ToolImportance.SUPPORTING
    required: bool = False
    access_mode: AccessMode = AccessMode.EXECUTE
    metadata: Dict[str, Any] = Field(default_factory=dict)

class TeamToolAssignmentUpdate(BaseModel):
    importance: Optional[ToolImportance] = None
    required: Optional[bool] = None
    access_mode: Optional[AccessMode] = None
    status: Optional[TeamToolStatus] = None
    metadata: Optional[Dict[str, Any]] = None

class TeamToolAssignmentResponse(BaseModel):
    id: str
    team_id: str
    tool_id: str
    importance: ToolImportance
    required: bool
    access_mode: AccessMode
    status: TeamToolStatus
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
