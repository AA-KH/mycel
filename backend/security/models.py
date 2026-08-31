from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

class ActionType(str, Enum):
    LLM_CALL = "LLM_CALL"
    TOOL_EXECUTION = "TOOL_EXECUTION"
    AGENT_HANDOFF = "AGENT_HANDOFF"
    ARTIFACT_ACCESS = "ARTIFACT_ACCESS"
    EXTERNAL_API_CALL = "EXTERNAL_API_CALL"
    EXTERNAL_MESSAGE = "EXTERNAL_MESSAGE"
    FILE_OPERATION = "FILE_OPERATION"
    DATABASE_OPERATION = "DATABASE_OPERATION"
    AUTONOMOUS_DECISION = "AUTONOMOUS_DECISION"
    DEPLOYMENT = "DEPLOYMENT"
    DATA_ACCESS = "DATA_ACCESS"

class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class SecurityDecisionStatus(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"
    REQUIRE_REVIEW = "REQUIRE_REVIEW"
    ERROR = "ERROR"

class SecurityContext(BaseModel):
    """Immutable context about the actor for evaluation."""
    organization_id: Optional[str] = None
    team_id: Optional[str] = None
    employee_id: Optional[str] = None
    agent_id: Optional[str] = None
    task_id: Optional[str] = None
    objective_id: Optional[str] = None
    session_id: Optional[str] = None
    capabilities: List[str] = Field(default_factory=list)
    environment: str = "development"

class SecurityRequest(BaseModel):
    """Structured context for security evaluation without raw sensitive payloads."""
    request_id: str
    trace_id: str
    context: SecurityContext
    action_type: ActionType
    resource: str
    intent: str
    payload_metadata: Dict[str, Any] = Field(default_factory=dict)
    tool_id: Optional[str] = None
    target_agent_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SecurityDecision(BaseModel):
    """Output of the SecurityGateway evaluation."""
    decision_id: str
    request_id: str
    status: SecurityDecisionStatus
    reason: str
    risk_level: RiskLevel
    policy_id: Optional[str] = None
    provider_result: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    audit_reference: Optional[str] = None

class SecurityAuditEvent(BaseModel):
    """Immutable record for the audit log."""
    event_id: str
    request: SecurityRequest
    decision: SecurityDecision
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
