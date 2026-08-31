from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

from .models import (
    PositionStatus, PositionType, Seniority, Criticality,
    PositionSkillRequirement, PositionToolRequirement,
    PositionKnowledgeRequirement, PositionReasoningRequirement,
    WorkforceRequirement
)

class PositionCreate(BaseModel):
    position_id: str
    team_id: str
    name: str
    display_name: str
    description: str = ""
    purpose: str = ""
    position_type: PositionType = PositionType.INDIVIDUAL_CONTRIBUTOR
    seniority: Seniority = Seniority.MID
    criticality: Criticality = Criticality.MEDIUM
    responsibilities: List[str] = []
    workforce: WorkforceRequirement = WorkforceRequirement()
    required_skills: List[PositionSkillRequirement] = []
    required_tools: List[PositionToolRequirement] = []
    required_knowledge: List[PositionKnowledgeRequirement] = []
    reasoning_requirements: List[PositionReasoningRequirement] = []
    pipeline_responsibilities: List[str] = []
    stage_responsibilities: List[str] = []
    output_responsibilities: List[str] = []
    quality_responsibilities: List[str] = []
    metadata: Dict[str, Any] = {}

class PositionResponse(BaseModel):
    id: str
    position_id: str
    team_id: str
    name: str
    display_name: str
    description: str
    purpose: str
    version: str
    status: PositionStatus
    position_type: PositionType
    seniority: Seniority
    criticality: Criticality
    responsibilities: List[str]
    workforce: WorkforceRequirement
    required_skills: List[PositionSkillRequirement]
    required_tools: List[PositionToolRequirement]
    required_knowledge: List[PositionKnowledgeRequirement]
    reasoning_requirements: List[PositionReasoningRequirement]
    pipeline_responsibilities: List[str]
    stage_responsibilities: List[str]
    output_responsibilities: List[str]
    quality_responsibilities: List[str]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
