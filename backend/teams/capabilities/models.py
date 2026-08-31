from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone

class TeamCapabilityProfile(BaseModel):
    team_id: str
    team_version: str = "1.0.0"
    
    skills: List[str] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)
    knowledge: List[str] = Field(default_factory=list)
    reasoning: List[str] = Field(default_factory=list)
    
    pipelines: List[str] = Field(default_factory=list)
    stages: List[str] = Field(default_factory=list)
    outputs: List[str] = Field(default_factory=list)
    quality_requirements: List[str] = Field(default_factory=list)
    
    positions: List[str] = Field(default_factory=list)
    
    workforce_summary: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    resolved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TeamCapabilityResolutionResult(BaseModel):
    team_id: str
    profile: Optional[TeamCapabilityProfile] = None
    resolved: bool = False
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    resolved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
