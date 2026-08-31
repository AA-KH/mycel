from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from enum import Enum

from .models import QualityGateDecision

class QualityCheckResultStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    SKIPPED = "skipped"
    ERROR = "error"
    PENDING = "pending"

class QualityCheckResult(BaseModel):
    check_id: str
    status: QualityCheckResultStatus
    score: Optional[int] = None
    threshold: Optional[int] = None
    message: str = ""
    evidence: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    executed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class QualityGateResult(BaseModel):
    id: Optional[str] = None
    quality_gate_id: str
    version: str
    
    execution_id: str
    stage_execution_id: Optional[str] = None
    pipeline_execution_id: Optional[str] = None
    
    decision: QualityGateDecision
    score: Optional[int] = None
    
    check_results: List[QualityCheckResult] = Field(default_factory=list)
    failure_reasons: List[str] = Field(default_factory=list)
    evidence: Dict[str, Any] = Field(default_factory=dict)
    
    metadata: Dict[str, Any] = Field(default_factory=dict)
    executed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
