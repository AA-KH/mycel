from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

from .models import ReasoningPolicies, ReasoningProfileStatus

class TeamReasoningProfileCreate(BaseModel):
    name: str
    display_name: str
    description: str
    principles: List[str]
    policies: ReasoningPolicies

class TeamReasoningProfileResponse(BaseModel):
    id: str
    team_id: str
    name: str
    display_name: str
    description: str
    version: str
    status: ReasoningProfileStatus
    principles: List[str]
    policies: ReasoningPolicies
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

class StrategyAssignmentResponse(BaseModel):
    id: str
    strategy_id: str
    priority: int
    required: bool
    status: str

class ResolvedTeamReasoningResponse(BaseModel):
    profile: TeamReasoningProfileResponse
    strategies: List[StrategyAssignmentResponse]
