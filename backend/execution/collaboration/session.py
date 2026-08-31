"""
Multi-Agent Collaboration Session & Protocol Domain Models (Phase 11)

Defines models for:
- CollaborationSession & CollaborationSessionStatus
- CollaborationMessage & MessageType
- CollaborationHandoff & HandoffAckStatus
- CollaborationClarification
- CollaborationContext (Minimal Context Projection)
- CollaborationErrorCode

Strict Invariants:
- No unrestricted agent chat / message bus.
- No transmission of secrets, API keys, credentials, or private team tools.
- No transmission of hidden reasoning / chain-of-thought.
- Communication takes place via structured handoffs & ArtifactReferences only.
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone


# ─────────────────────────────────────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────────────────────────────────────

class CollaborationSessionStatus(str, Enum):
    CREATED = "CREATED"
    VALIDATING = "VALIDATING"
    READY = "READY"
    WAITING_FOR_INPUT = "WAITING_FOR_INPUT"
    ACTIVE = "ACTIVE"
    WAITING_FOR_OUTPUT = "WAITING_FOR_OUTPUT"
    HANDOFF_READY = "HANDOFF_READY"
    COMPLETED = "COMPLETED"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class MessageType(str, Enum):
    REQUEST = "REQUEST"
    RESPONSE = "RESPONSE"
    HANDOFF = "HANDOFF"
    STATUS = "STATUS"
    ERROR = "ERROR"
    APPROVAL_REQUEST = "APPROVAL_REQUEST"
    APPROVAL_RESULT = "APPROVAL_RESULT"


class HandoffAckStatus(str, Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    NEEDS_CLARIFICATION = "NEEDS_CLARIFICATION"
    BLOCKED = "BLOCKED"


class CollaborationErrorCode(str, Enum):
    CONTRACT_INVALID = "CONTRACT_INVALID"
    SCHEMA_INVALID = "SCHEMA_INVALID"
    SOURCE_NOT_ALLOWED = "SOURCE_NOT_ALLOWED"
    TARGET_NOT_ALLOWED = "TARGET_NOT_ALLOWED"
    MISSING_INPUT = "MISSING_INPUT"
    ARTIFACT_INVALID = "ARTIFACT_INVALID"
    ARTIFACT_NOT_FOUND = "ARTIFACT_NOT_FOUND"
    QUALITY_REQUIREMENT_NOT_MET = "QUALITY_REQUIREMENT_NOT_MET"
    DEPENDENCY_INVALID = "DEPENDENCY_INVALID"
    COLLABORATION_LOOP = "COLLABORATION_LOOP"
    MAX_RETRIES_EXCEEDED = "MAX_RETRIES_EXCEEDED"
    MAX_CLARIFICATIONS_EXCEEDED = "MAX_CLARIFICATIONS_EXCEEDED"


class ClarificationSessionStatus(str, Enum):
    PENDING = "PENDING"
    RESOLVED = "RESOLVED"
    EXPIRED = "EXPIRED"


# ─────────────────────────────────────────────────────────────────────────────
# Artifact Reference Model (Lightweight Pointer)
# ─────────────────────────────────────────────────────────────────────────────

class ArtifactReference(BaseModel):
    artifact_id: str
    artifact_type: str                  # e.g. "research_report", "video", "landing_page"
    format: Optional[str] = None         # e.g. "pdf", "mp4", "json"
    uri: Optional[str] = None            # Storage reference (NO credentials)
    description: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ─────────────────────────────────────────────────────────────────────────────
# Collaboration Message
# ─────────────────────────────────────────────────────────────────────────────

class CollaborationMessage(BaseModel):
    message_id: str
    session_id: str
    task_id: str
    source_work_unit_id: str
    target_work_unit_id: str
    message_type: MessageType = MessageType.HANDOFF
    protocol_version: str = "1.0"
    payload: Dict[str, Any] = Field(default_factory=dict)
    artifact_references: List[ArtifactReference] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ─────────────────────────────────────────────────────────────────────────────
# Collaboration Handoff
# ─────────────────────────────────────────────────────────────────────────────

class CollaborationHandoff(BaseModel):
    handoff_id: str
    session_id: str
    source_work_unit_id: str
    target_work_unit_id: str
    contract_id: str
    input_references: List[str] = Field(default_factory=list)
    output_references: List[str] = Field(default_factory=list)
    payload: Dict[str, Any] = Field(default_factory=dict)
    artifact_references: List[ArtifactReference] = Field(default_factory=list)
    summary: str = ""
    status: HandoffAckStatus = HandoffAckStatus.ACCEPTED
    validation_errors: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ─────────────────────────────────────────────────────────────────────────────
# Collaboration Clarification
# ─────────────────────────────────────────────────────────────────────────────

class CollaborationClarification(BaseModel):
    clarification_id: str
    session_id: str
    question: str
    required_input: str
    reason: str
    status: ClarificationSessionStatus = ClarificationSessionStatus.PENDING
    response_payload: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ─────────────────────────────────────────────────────────────────────────────
# Minimal Collaboration Context (Context Projection)
# ─────────────────────────────────────────────────────────────────────────────

class CollaborationContext(BaseModel):
    """
    Pruned minimal context passed to receiving WorkUnit.

    Strict Invariants:
        - NO chain-of-thought / hidden reasoning traces.
        - NO internal team tools of other teams.
        - NO private team knowledge spaces.
        - NO credentials, tokens, or API keys.
    """
    task_id: str
    work_unit_id: str
    objective: str
    constraints: Dict[str, Any] = Field(default_factory=dict)
    required_inputs: List[str] = Field(default_factory=list)
    received_outputs: Dict[str, Any] = Field(default_factory=dict)
    artifact_references: List[ArtifactReference] = Field(default_factory=list)
    relevant_contract_id: Optional[str] = None
    quality_requirements: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ─────────────────────────────────────────────────────────────────────────────
# Collaboration Session Aggregate
# ─────────────────────────────────────────────────────────────────────────────

class CollaborationSession(BaseModel):
    session_id: str
    task_id: str
    source_work_unit_id: str
    target_work_unit_id: str
    source_team_id: str
    target_team_id: str
    contract_id: str
    status: CollaborationSessionStatus = CollaborationSessionStatus.CREATED
    handoff_count: int = 0
    clarification_count: int = 0
    max_handoffs: int = 5
    max_clarifications: int = 2
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def is_active(self) -> bool:
        return self.status in (
            CollaborationSessionStatus.CREATED,
            CollaborationSessionStatus.VALIDATING,
            CollaborationSessionStatus.READY,
            CollaborationSessionStatus.ACTIVE,
            CollaborationSessionStatus.HANDOFF_READY,
            CollaborationSessionStatus.WAITING_FOR_INPUT,
            CollaborationSessionStatus.WAITING_FOR_OUTPUT,
        )

    @property
    def is_terminal(self) -> bool:
        return self.status in (
            CollaborationSessionStatus.COMPLETED,
            CollaborationSessionStatus.BLOCKED,
            CollaborationSessionStatus.FAILED,
            CollaborationSessionStatus.CANCELLED,
        )
