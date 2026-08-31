from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

class TeamToolStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"

class ToolImportance(str, Enum):
    CORE = "core"
    SUPPORTING = "supporting"
    OPTIONAL = "optional"

class AccessMode(str, Enum):
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    FULL = "full"

class TeamToolAssignment(BaseModel):
    """
    Association between a Team and an available Tool.
    """
    id: Optional[str] = None
    team_id: str
    tool_id: str
    required: bool = False
    importance: ToolImportance = ToolImportance.SUPPORTING
    access_mode: AccessMode = AccessMode.EXECUTE
    status: TeamToolStatus = TeamToolStatus.ACTIVE
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
