"""
Company Builder Delegation Models

Provides structured transparency into how work is delegated:
Manager --> Team Members with explicit task assignments.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid


class MemberAssignment(BaseModel):
    """Represents a single task assigned to a specific team member."""
    member_id: str
    member_name: str
    member_role: str
    member_avatar: Optional[str] = None
    task_title: str
    task_description: str
    expected_output: str
    status: str = "ASSIGNED"  # ASSIGNED | IN_PROGRESS | DONE
    team_color: Optional[str] = None


class TeamDelegation(BaseModel):
    """Represents a manager delegating work to their team."""
    team_id: str
    team_name: str
    team_color: str
    manager_name: str
    manager_role: str
    manager_avatar: Optional[str] = None
    objective: str
    members: List[MemberAssignment] = Field(default_factory=list)


class DelegationGraph(BaseModel):
    """
    Full delegation transparency graph for a given pipeline stage.
    This is what gets sent to the frontend to render the node tree.
    """
    graph_id: str = Field(default_factory=lambda: f"dg_{uuid.uuid4().hex[:8]}")
    workflow_id: str
    stage: str
    prompt_summary: str
    teams: List[TeamDelegation] = Field(default_factory=list)
    total_members_assigned: int = 0
    total_tasks: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def compute_totals(self):
        self.total_tasks = sum(len(t.members) for t in self.teams)
        self.total_members_assigned = self.total_tasks


class OutputDocument(BaseModel):
    """Represents a generated output artifact (PDF, HTML, etc.)."""
    doc_id: str = Field(default_factory=lambda: f"doc_{uuid.uuid4().hex[:8]}")
    workflow_id: str
    stage: str
    title: str
    format: str  # "pdf" | "html" | "pptx"
    content_html: str  # HTML representation (can be converted to PDF)
    download_url: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
