"""
Domain models for the Employee / Agent Definition system.
Represents unique AI employees and their capabilities.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class EmployeeStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    RETIRED = "retired"

class EmployeeAvailability(str, Enum):
    AVAILABLE = "available"
    BUSY = "busy"
    OFFLINE = "offline"

class EmployeeIdentity(BaseModel):
    title: str
    specialization: str
    summary: str
    personality: str
    communication_style: str
    experience_level: str


class PersonalityTraits(BaseModel):
    analytical: int = Field(ge=0, le=100, default=50)
    cautious: int = Field(ge=0, le=100, default=50)
    proactive: int = Field(ge=0, le=100, default=50)


class Personality(BaseModel):
    traits: PersonalityTraits = Field(default_factory=PersonalityTraits)
    communication_style: str
    decision_style: str


class Experience(BaseModel):
    level: str
    years_equivalent: int = Field(ge=0)
    domains: List[str] = Field(default_factory=list)


class SkillProficiency(BaseModel):
    level: int = Field(ge=0, le=100)
    experience: str


class ToolPermission(str, Enum):
    ALLOWED = "allowed"
    APPROVAL_REQUIRED = "approval_required"
    DENIED = "denied"


class MemoryConfig(BaseModel):
    working_memory: bool = True
    episodic_memory: bool = True
    semantic_memory: bool = True
    procedural_memory: bool = False
    retention_days: int = Field(ge=0, default=90)


class PerformanceSummary(BaseModel):
    overall_score: float = Field(ge=0.0, le=100.0, default=0.0)
    quality_score: float = Field(ge=0.0, le=100.0, default=0.0)
    reliability_score: float = Field(ge=0.0, le=100.0, default=0.0)
    tool_success_rate: float = Field(ge=0.0, le=100.0, default=0.0)
    tasks_completed: int = Field(ge=0, default=0)


class Employee(BaseModel):
    """
    The canonical definition of a Unique AI Employee.
    This defines WHO the agent is and WHAT capabilities it has.
    """
    employee_id: str
    company_id: str
    department_id: str
    team_id: str
    position_id: str
    
    name: str
    display_name: str
    identity: EmployeeIdentity
    
    personality: Personality
    experience: Experience
    
    skills: Dict[str, SkillProficiency] = Field(default_factory=dict)
    
    reasoning_profile_id: str
    
    tools: List[str] = Field(default_factory=list)
    permissions: Dict[str, ToolPermission] = Field(default_factory=dict)
    outputs: List[str] = Field(default_factory=list)
    constraints: Dict[str, Any] = Field(default_factory=dict)
    
    memory_config: MemoryConfig = Field(default_factory=MemoryConfig)
    performance_summary: PerformanceSummary = Field(default_factory=PerformanceSummary)
    
    status: EmployeeStatus = EmployeeStatus.DRAFT
    availability: EmployeeAvailability = EmployeeAvailability.OFFLINE
    version: str = "1.0.0"
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
