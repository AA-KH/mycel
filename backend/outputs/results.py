from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from enum import Enum

class OutputViolationSeverity(str, Enum):
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class OutputViolation(BaseModel):
    field: str
    expected: Any
    actual: Any
    severity: OutputViolationSeverity = OutputViolationSeverity.ERROR
    code: str
    message: str

class OutputValidationResult(BaseModel):
    valid: bool
    contract_id: str
    contract_version: str
    actual_output: Dict[str, Any] # Usually contains artifact_id or other logical reference
    
    violations: List[OutputViolation] = Field(default_factory=list)
    warnings: List[OutputViolation] = Field(default_factory=list)
    evidence: Dict[str, Any] = Field(default_factory=dict)
    
    validated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
