"""
Memory System Domain Models (Phase 12)

Defines models for:
- MemoryScope (ORGANIZATION, TEAM, POSITION, EMPLOYEE, AGENT, TASK, COLLABORATION)
- MemoryType (EPISODIC, SEMANTIC, PROCEDURAL, DECISION, LESSON)
- MemoryImportance & MemoryStatus
- MemoryItem (Aggregate Root)
- MemoryQueryResult & MemoryExtractRequest

Strict Boundaries:
- Memory is NOT Knowledge (curated manual).
- Memory is NOT Chat History (raw transcripts).
- Memory is NOT Artifact Storage (deliverable binaries).
- Memory is NOT Context (temporary runtime projection).
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from execution.collaboration.session import ArtifactReference


# ─────────────────────────────────────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────────────────────────────────────

class MemoryScope(str, Enum):
    ORGANIZATION = "ORGANIZATION"
    TEAM = "TEAM"
    POSITION = "POSITION"
    EMPLOYEE = "EMPLOYEE"
    AGENT = "AGENT"
    TASK = "TASK"
    COLLABORATION = "COLLABORATION"


class MemoryType(str, Enum):
    EPISODIC = "EPISODIC"       # Events, milestones, execution summaries
    SEMANTIC = "SEMANTIC"       # Facts, rules, learned preferences
    PROCEDURAL = "PROCEDURAL"   # Best practice steps, workflow shortcuts
    DECISION = "DECISION"       # Choices made, rationale, trade-offs
    LESSON = "LESSON"           # Identified mistakes, quality gate feedback


class MemoryImportance(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class MemoryStatus(str, Enum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"
    SUPERSEDED = "SUPERSEDED"
    EXPIRED = "EXPIRED"
    DELETED = "DELETED"


# ─────────────────────────────────────────────────────────────────────────────
# Memory Item Aggregate Root
# ─────────────────────────────────────────────────────────────────────────────

class MemoryItem(BaseModel):
    memory_id: str
    organization_id: str = "mycel_global"
    scope: MemoryScope = MemoryScope.TEAM
    scope_id: str                         # e.g., "developer", "emp_dev_001", "task_123"
    memory_type: MemoryType = MemoryType.SEMANTIC
    importance: MemoryImportance = MemoryImportance.MEDIUM
    status: MemoryStatus = MemoryStatus.ACTIVE

    title: str
    content: str                          # Summarized insight / rule (NO raw transcript)
    summary: str = ""
    tags: List[str] = Field(default_factory=list)

    # Provenance tracking
    source_task_id: Optional[str] = None
    source_work_unit_id: Optional[str] = None
    source_employee_id: Optional[str] = None
    source_team_id: Optional[str] = None
    artifact_references: List[ArtifactReference] = Field(default_factory=list)

    confidence: float = 1.0               # Deterministic confidence (0.0 to 1.0)
    superseded_by: Optional[str] = None   # Points to memory_id of newer replacement item

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def is_active(self) -> bool:
        return self.status == MemoryStatus.ACTIVE


# ─────────────────────────────────────────────────────────────────────────────
# Search & Extraction Models
# ─────────────────────────────────────────────────────────────────────────────

class MemoryQueryResult(BaseModel):
    memory_item: MemoryItem
    score: float                          # Relevance score
    match_reason: str = ""


class MemoryExtractRequest(BaseModel):
    task_id: str
    work_unit_id: Optional[str] = None
    employee_id: Optional[str] = None
    team_id: Optional[str] = None
    experience_type: MemoryType = MemoryType.EPISODIC
    raw_text_or_data: str
    importance: MemoryImportance = MemoryImportance.MEDIUM
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
