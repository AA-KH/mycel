"""
API schemas for Employee endpoints.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from .models import (
    EmployeeStatus, EmployeeAvailability, EmployeeIdentity, Personality, Experience,
    SkillProficiency, ToolPermission, MemoryConfig,
    PerformanceSummary
)


class EmployeeCreate(BaseModel):
    employee_id: str
    company_id: str
    department_id: str
    team_id: str
    position_id: str
    
    name: str = Field(..., min_length=1, max_length=100)
    display_name: str = Field(..., min_length=1, max_length=50)
    identity: EmployeeIdentity
    
    personality: Personality
    experience: Experience
    
    skills: Dict[str, SkillProficiency] = Field(default_factory=dict)
    reasoning_profile_id: str
    
    tools: List[str] = Field(default_factory=list)
    permissions: Dict[str, ToolPermission] = Field(default_factory=dict)
    outputs: List[str] = Field(default_factory=list)
    constraints: Dict[str, Any] = Field(default_factory=dict)
    
    memory_config: Optional[MemoryConfig] = None
    
    status: EmployeeStatus = EmployeeStatus.DRAFT
    availability: EmployeeAvailability = EmployeeAvailability.OFFLINE
    version: str = "1.0.0"


class EmployeeUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    display_name: Optional[str] = Field(None, min_length=1, max_length=50)
    identity: Optional[EmployeeIdentity] = None
    
    personality: Optional[Personality] = None
    experience: Optional[Experience] = None
    
    skills: Optional[Dict[str, SkillProficiency]] = None
    reasoning_profile_id: Optional[str] = None
    
    tools: Optional[List[str]] = None
    permissions: Optional[Dict[str, ToolPermission]] = None
    outputs: Optional[List[str]] = None
    constraints: Optional[Dict[str, Any]] = None
    
    memory_config: Optional[MemoryConfig] = None
    version: Optional[str] = None


class EmployeeStatusUpdate(BaseModel):
    status: EmployeeStatus

class EmployeeAvailabilityUpdate(BaseModel):
    availability: EmployeeAvailability


class EmployeeResponse(BaseModel):
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
    
    skills: Dict[str, SkillProficiency]
    reasoning_profile_id: str
    
    tools: List[str]
    permissions: Dict[str, ToolPermission]
    outputs: List[str]
    constraints: Dict[str, Any]
    
    memory_config: MemoryConfig
    performance_summary: PerformanceSummary
    
    status: EmployeeStatus
    availability: EmployeeAvailability
    version: str
    
    created_at: datetime
    updated_at: datetime


class EmployeeProfileResponse(BaseModel):
    """
    Sanitized profile for the frontend Pixel Office.
    Omits sensitive internal implementation details (e.g., hidden system config).
    """
    employee_id: str
    name: str
    display_name: str
    title: str
    specialization: str
    summary: str
    
    department_id: str
    team_id: str
    position_id: str
    
    skills: Dict[str, int]  # Only expose skill level visually
    tools: List[str]
    outputs: List[str]
    
    performance_score: float
    status: EmployeeStatus
    availability: EmployeeAvailability
