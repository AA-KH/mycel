from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

class ToolRequest(BaseModel):
    execution_id: str
    employee_id: str
    tool_name: str
    arguments: Dict[str, Any]
    reason: str

class ToolResult(BaseModel):
    tool_name: str
    status: str # "success" or "error"
    output: Any
    artifact_ids: List[str] = Field(default_factory=list)
    error: Optional[str] = None
    duration_ms: int = 0

class VerificationResult(BaseModel):
    status: str # "passed" or "failed"
    checks: List[Dict[str, str]] = Field(default_factory=list)
    reason: Optional[str] = None

class ExecutionResult(BaseModel):
    execution_id: str
    employee_id: str
    task_id: str
    status: str # "completed", "failed", "cancelled", "timed_out"
    
    output: Dict[str, Any] = Field(default_factory=dict) # e.g. {"type": "text", "content": "..."}
    artifacts: List[str] = Field(default_factory=list)
    verification: VerificationResult
    
    metrics: Dict[str, Any] = Field(default_factory=dict)
    
    error: Optional[str] = None
    completed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
