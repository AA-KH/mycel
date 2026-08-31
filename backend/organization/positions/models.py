from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from organization.types import Level, PositionRequirements

class Position(BaseModel):
    id: Optional[str] = None
    company_id: str
    department_id: Optional[str] = None
    team_id: str
    title: str
    slug: str
    description: Optional[str] = None
    level: Level = Level.MID
    status: str = "open"  # open, closed, archived
    responsibilities: List[str] = Field(default_factory=list)
    requirements: PositionRequirements = Field(default_factory=PositionRequirements)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
