"""
Orchestration Events — Real-time event contracts for the HR/Workforce orchestration pipeline.
"""

import logging
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from api.v1.routes.realtime import manager
from core.mongodb import mongodb_connection

logger = logging.getLogger(__name__)

# ── Phase Enum ────────────────────────────────────────────────────────

class OrchestrationPhase(str, Enum):
    TASK_RECEIVED = "TASK_RECEIVED"
    HR_ANALYSIS_STARTED = "HR_ANALYSIS_STARTED"
    CAPABILITY_IDENTIFIED = "CAPABILITY_IDENTIFIED"
    TEAM_SELECTION_STARTED = "TEAM_SELECTION_STARTED"
    TEAM_SELECTED = "TEAM_SELECTED"
    MEMBER_SELECTION_STARTED = "MEMBER_SELECTION_STARTED"
    MEMBER_SELECTED = "MEMBER_SELECTED"
    TEAM_ASSEMBLED = "TEAM_ASSEMBLED"
    WORKFORCE_ASSEMBLED = "WORKFORCE_ASSEMBLED"
    TASK_ASSIGNED = "TASK_ASSIGNED"
    AGENT_MOVING = "AGENT_MOVING"
    EXECUTION_STARTED = "EXECUTION_STARTED"
    AGENT_WORKING = "AGENT_WORKING"
    AGENT_COMPLETED = "AGENT_COMPLETED"
    AGENT_FAILED = "AGENT_FAILED"
    ORCHESTRATION_COMPLETED = "ORCHESTRATION_COMPLETED"
    ORCHESTRATION_FAILED = "ORCHESTRATION_FAILED"

_PHASE_ORDER: List[OrchestrationPhase] = [
    OrchestrationPhase.TASK_RECEIVED,
    OrchestrationPhase.HR_ANALYSIS_STARTED,
    OrchestrationPhase.CAPABILITY_IDENTIFIED,
    OrchestrationPhase.TEAM_SELECTION_STARTED,
    OrchestrationPhase.TEAM_SELECTED,
    OrchestrationPhase.MEMBER_SELECTION_STARTED,
    OrchestrationPhase.MEMBER_SELECTED,
    OrchestrationPhase.TEAM_ASSEMBLED,
    OrchestrationPhase.WORKFORCE_ASSEMBLED,
    OrchestrationPhase.TASK_ASSIGNED,
    OrchestrationPhase.AGENT_MOVING,
    OrchestrationPhase.EXECUTION_STARTED,
    OrchestrationPhase.AGENT_WORKING,
    OrchestrationPhase.AGENT_COMPLETED,
    OrchestrationPhase.AGENT_FAILED,
    OrchestrationPhase.ORCHESTRATION_COMPLETED,
    OrchestrationPhase.ORCHESTRATION_FAILED,
]

def _phase_index(phase: OrchestrationPhase) -> int:
    try:
        return _PHASE_ORDER.index(phase)
    except ValueError:
        return -1

# ── Event Model ───────────────────────────────────────────────────────

class OrchestrationPayload(BaseModel):
    detail: Optional[str] = None
    team_id: Optional[str] = None
    team_name: Optional[str] = None
    employee_id: Optional[str] = None
    employee_name: Optional[str] = None
    employee_role: Optional[str] = None
    session_id: Optional[str] = None
    wallet_card_id: Optional[str] = None
    subtask_id: Optional[str] = None
    match_score: Optional[float] = None
    capabilities: Optional[List[str]] = None
    selected_teams: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    # legacy fields for transition safety if any components rely on it
    subtask_index: Optional[int] = None
    total_subtasks: Optional[int] = None

class OrchestrationEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str
    event_type: str = "orchestration_phase"
    phase: OrchestrationPhase
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    actor: str = "system"
    payload: OrchestrationPayload

# ── Emit Helper ───────────────────────────────────────────────────────

async def emit_orchestration_event(
    task_id: str,
    phase: OrchestrationPhase,
    actor: str = "system",
    **payload_kwargs
) -> None:
    """
    Fire-and-forget: broadcast an orchestration phase event over the existing
    WebSocket infrastructure AND persist it to the task's orchestration history
    in MongoDB.
    """
    event = OrchestrationEvent(
        task_id=task_id,
        phase=phase,
        actor=actor,
        payload=OrchestrationPayload(**payload_kwargs)
    )

    # For frontend convenience in sorting, inject the phase_index manually during dump
    dumped_event = event.model_dump(exclude_none=True)
    dumped_event["phase_index"] = _phase_index(phase)

    # 1. Broadcast over WebSocket (real-time)
    try:
        await manager.broadcast(task_id, dumped_event)
        logger.debug(f"Orchestration event broadcast: {phase.value} for task {task_id}")
    except Exception as e:
        logger.error(f"Failed to broadcast orchestration event: {e}")

    # 2. Persist to MongoDB (audit trail)
    try:
        db = mongodb_connection.db
        
        # Strip the redundant event_type property to save space in the DB array, 
        # but store everything else so it perfectly reconstructs the history
        persist_record = {k: v for k, v in dumped_event.items() if k != "event_type"}
        
        await db.task_logs.update_one(
            {"task_id": task_id},
            {"$push": {"orchestration_events": persist_record}},
        )
    except Exception as e:
        logger.error(f"Failed to persist orchestration event: {e}")
