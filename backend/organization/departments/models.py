from datetime import datetime, timezone
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from organization.types import CompanyStatus

class Department(BaseModel):
    id: Optional[str] = None
    company_id: str
    name: str
    slug: str
    description: Optional[str] = None
    status: CompanyStatus = CompanyStatus.DRAFT
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
