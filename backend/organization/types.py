from enum import Enum
from typing import List
from pydantic import BaseModel, Field

class CompanyStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"

class Level(str, Enum):
    INTERN = "intern"
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    MANAGER = "manager"
    DIRECTOR = "director"
    EXECUTIVE = "executive"

class CapabilityRequirement(BaseModel):
    capability: str
    minimum_level: int = Field(ge=0, le=100)
    required: bool = True

class PositionRequirements(BaseModel):
    capabilities: List[CapabilityRequirement] = Field(default_factory=list)
