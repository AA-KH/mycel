from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from organization.types import CompanyStatus

class TeamCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    slug: str = Field(..., min_length=1, max_length=100, pattern=r'^[a-z0-9-]+$')
    description: Optional[str] = None
    mission: Optional[str] = None
    status: CompanyStatus = CompanyStatus.DRAFT
    metadata: Dict[str, Any] = Field(default_factory=dict)

class TeamUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    mission: Optional[str] = None
    status: Optional[CompanyStatus] = None
    metadata: Optional[Dict[str, Any]] = None

class TeamResponse(BaseModel):
    id: str
    company_id: str
    department_id: Optional[str] = None
    name: str
    slug: str
    description: Optional[str] = None
    mission: Optional[str] = None
    status: CompanyStatus
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
