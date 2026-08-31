from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ── Legacy API Schemas (Preserved for compatibility) ───────────────────────

class TaskSubmitRequest(BaseModel):
    task: str = Field(..., min_length=10, max_length=2000, description="The project task description")
    submitted_by: str = Field(default="human", description="Who submitted the task")


class TaskSubmitResponse(BaseModel):
    task_id: str
    status: str
    message: str
    subtasks: Optional[List[Dict[str, Any]]] = None


class TeamResultSchema(BaseModel):
    team: str
    subtask: str
    result: str
    completed_at: Optional[str] = None


class TaskLogSchema(BaseModel):
    task_id: str
    project_task: str
    submitted_at: str
    submitted_by: str
    status: str
    manager_plan: Optional[dict] = None
    team_results: List[TeamResultSchema] = []
    final_report: Optional[str] = None
    completed_at: Optional[str] = None
    total_duration_seconds: Optional[int] = None


# ── Phase 10 Task Orchestration API Schemas ────────────────────────────────

class TaskOrchestrateRequest(BaseModel):
    user_input: str = Field(..., min_length=3, max_length=5000, description="User request text")
    organization_id: str = Field(default="mycel_global", description="Organization ID")
    context: Optional[Dict[str, Any]] = None
    constraints: Optional[Dict[str, Any]] = None


class TaskOrchestrateResponse(BaseModel):
    task_id: str
    plan_id: Optional[str] = None
    status: str
    work_unit_count: int = 0
    required_outputs: List[str] = Field(default_factory=list)
    clarifications: List[Dict[str, Any]] = Field(default_factory=list)
    blockers: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[Dict[str, Any]] = Field(default_factory=list)
    plan: Optional[Dict[str, Any]] = None


class ResolveClarificationRequest(BaseModel):
    clarification_id: str = Field(..., description="Clarification ID to resolve")
    response_text: str = Field(..., min_length=1, description="User response text")


# ── Phase 11 Multi-Agent Collaboration API Schemas ────────────────────────

class CreateCollaborationSessionRequest(BaseModel):
    source_work_unit_id: str = Field(..., description="Source WorkUnit ID")
    target_work_unit_id: str = Field(..., description="Target WorkUnit ID")


class CreateHandoffRequest(BaseModel):
    payload: Dict[str, Any] = Field(default_factory=dict, description="Structured handoff payload")
    artifact_references: List[Dict[str, Any]] = Field(default_factory=list, description="Artifact references")
    summary: str = Field(default="", description="Summary of handoff")


class AcknowledgeHandoffRequest(BaseModel):
    handoff_id: str = Field(..., description="Handoff ID")
    status: str = Field(..., description="ACCEPTED or REJECTED")
    feedback: str = Field(default="", description="Feedback if rejected")


class SubmitClarificationRequest(BaseModel):
    question: str = Field(..., description="Question text")
    required_input: str = Field(..., description="Input key required")
    reason: str = Field(default="", description="Reason for clarification")


# ── Phase 12 Memory System API Schemas ─────────────────────────────────────

class RecordMemoryRequest(BaseModel):
    scope: str = Field(..., description="MemoryScope (ORGANIZATION, TEAM, POSITION, EMPLOYEE, AGENT, TASK, COLLABORATION)")
    scope_id: str = Field(..., description="Scope ID (e.g. 'developer', 'emp_dev_001')")
    memory_type: str = Field(default="SEMANTIC", description="MemoryType (EPISODIC, SEMANTIC, PROCEDURAL, DECISION, LESSON)")
    importance: str = Field(default="MEDIUM", description="MemoryImportance (LOW, MEDIUM, HIGH, CRITICAL)")
    title: str = Field(..., min_length=3, description="Memory title")
    content: str = Field(..., min_length=3, description="Memory content summary")
    tags: List[str] = Field(default_factory=list, description="Tags for search indexing")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class QueryMemoryRequest(BaseModel):
    scope: str = Field(..., description="MemoryScope")
    scope_id: str = Field(..., description="Scope ID")
    keywords: Optional[List[str]] = Field(default=None, description="Search keywords")
    tags: Optional[List[str]] = Field(default=None, description="Search tags")
    limit: int = Field(default=5, description="Max results to return")
