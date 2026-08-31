from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from organization.types import CompanyStatus

class DepartmentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    slug: str = Field(..., min_length=1, max_length=100, pattern=r'^[a-z0-9-]+$')
    description: Optional[str] = None
    status: CompanyStatus = CompanyStatus.DRAFT
    metadata: Dict[str, Any] = Field(default_factory=dict)

class DepartmentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    status: Optional[CompanyStatus] = None
    metadata: Optional[Dict[str, Any]] = None

class DepartmentResponse(BaseModel):
    id: str
    company_id: str
    name: str
    slug: str
    description: Optional[str] = None
    status: CompanyStatus
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
