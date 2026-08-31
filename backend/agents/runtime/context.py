from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone
import uuid

class ExecutionContext(BaseModel):
    """
    Canonical ExecutionContext for the Agent Runtime.
    Flows through API -> Task -> Worker -> Runtime -> LLM -> Tool -> Artifact -> Event
    """
    execution_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str
    employee_id: str
    company_id: str
    
    # Optional organizational context
    request_id: Optional[str] = None
    correlation_id: Optional[str] = None
    department_id: Optional[str] = None
    team_id: Optional[str] = None
    position_id: Optional[str] = None
    user_id: Optional[str] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        frozen = True # Context should be mostly immutable after creation
