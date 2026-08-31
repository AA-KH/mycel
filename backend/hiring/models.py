from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime, timezone
import uuid

class SkillRequirement(BaseModel):
    skill_id: str
    minimum_proficiency: int = 0
    weight: float = 1.0
    required: bool = False

class ToolRequirement(BaseModel):
    tool_id: str
    required: bool = False

class OutputRequirement(BaseModel):
    type: str
    required: bool = False

class ReasoningRequirement(BaseModel):
    preferred: Optional[str] = None
    required: bool = False

class HiringRequirement(BaseModel):
    task_id: str
    company_id: str
    skills: List[SkillRequirement] = Field(default_factory=list)
    tools: List[ToolRequirement] = Field(default_factory=list)
    outputs: List[OutputRequirement] = Field(default_factory=list)
    reasoning_profile: ReasoningRequirement = Field(default_factory=ReasoningRequirement)

class CandidateSnapshot(BaseModel):
    employee_id: str
    name: str
    position_id: str
    specialization: str
    reasoning_profile_id: Optional[str] = None
    skills: Dict[str, int] = Field(default_factory=dict)
    tools: List[str] = Field(default_factory=list)
    outputs: List[str] = Field(default_factory=list)
    status: str
    availability: str

class HiringScoreBreakdown(BaseModel):
    skills: float = 0.0
    tools: float = 0.0
    outputs: float = 0.0
    reasoning: float = 0.0
    specialization: float = 0.0
    availability: float = 0.0

class HiringCandidateScore(BaseModel):
    employee_id: str
    overall_score: float
    breakdown: HiringScoreBreakdown
    eligible: bool = True
    ineligible_reasons: List[str] = Field(default_factory=list)

class HiringDecision(BaseModel):
    decision_id: str = Field(default_factory=lambda: f"dec_{uuid.uuid4().hex[:8]}")
    task_id: str
    company_id: str
    selected_employee_id: Optional[str] = None
    status: str  # "selected", "no_candidate"
    overall_score: Optional[float] = None
    candidate_count: int = 0
    selected_rank: Optional[int] = None
    reason_codes: List[str] = Field(default_factory=list)
    candidate_scores: List[HiringCandidateScore] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class EmployeeAssignment(BaseModel):
    assignment_id: str = Field(default_factory=lambda: f"asn_{uuid.uuid4().hex[:8]}")
    task_id: str
    employee_id: str
    decision_id: str
    assigned_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = "assigned"
