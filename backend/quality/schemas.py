from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

from .models import (
    QualityGateScope, QualityGateStatus, QualityCheckSeverity, QualityPolicy, QualityCheck
)

class QualityGateCreate(BaseModel):
    quality_gate_id: str
    name: str
    display_name: str
    description: str = ""
    scope: QualityGateScope
    severity: QualityCheckSeverity = QualityCheckSeverity.ERROR
    checks: List[QualityCheck] = []
    policy: QualityPolicy = QualityPolicy.ALL_REQUIRED_PASS
    minimum_score: Optional[int] = None

class QualityGateResponse(BaseModel):
    id: str
    quality_gate_id: str
    name: str
    display_name: str
    description: str
    scope: QualityGateScope
    version: str
    status: QualityGateStatus
    severity: QualityCheckSeverity
    checks: List[QualityCheck]
    policy: QualityPolicy
    minimum_score: Optional[int]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
