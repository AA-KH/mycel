"""
Team Execution Context (TOS 20)

A lightweight, immutable context object that carries the identity references
for a single unit of work within the Team Operating System.

This is NOT an execution engine. It does NOT:
    - instantiate agents
    - run pipelines
    - call LLMs
    - invoke tools
    - perform hiring
    - route tasks

It provides a stable identity frame that future runtime systems can use
to know exactly which contract, pipeline, position, and member own a
given unit of execution.
"""

from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime, timezone


class TeamExecutionContext(BaseModel):
    """
    Immutable execution identity context.

    Once created, treat this as immutable. If runtime state changes,
    create a new context or append a new event — do not mutate in place.
    """

    # Core identity
    context_id: str                             # stable unique identifier for this context
    team_id: str                                # owning team

    # Task reference
    task_id: Optional[str] = None

    # Contract references (IDs only — no live objects)
    execution_contract_id: Optional[str] = None
    collaboration_contract_id: Optional[str] = None

    # Pipeline reference
    pipeline_id: Optional[str] = None

    # Workforce references
    position_id: Optional[str] = None
    member_id: Optional[str] = None

    # Agent reference (future — not instantiated here)
    agent_id: Optional[str] = None

    # Context metadata
    initiated_by_team_id: Optional[str] = None  # if triggered via collaboration
    notes: str = ""

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(frozen=True)

    @property
    def is_collaborative(self) -> bool:
        """True if this context was initiated by a collaboration contract."""
        return self.collaboration_contract_id is not None

    @property
    def has_workforce_assignment(self) -> bool:
        """True if a position and member have been declared."""
        return bool(self.position_id and self.member_id)

    def summary(self) -> str:
        parts = [f"team={self.team_id}"]
        if self.task_id:
            parts.append(f"task={self.task_id}")
        if self.execution_contract_id:
            parts.append(f"contract={self.execution_contract_id}")
        if self.pipeline_id:
            parts.append(f"pipeline={self.pipeline_id}")
        if self.member_id:
            parts.append(f"member={self.member_id}")
        return f"TeamExecutionContext({', '.join(parts)})"
