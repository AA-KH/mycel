"""
Tasks Router — HTTP endpoints for task orchestration (Phase 10), multi-agent collaboration (Phase 11), and legacy task submission.
"""
import asyncio
import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException

from .schemas import (
    TaskSubmitRequest,
    TaskSubmitResponse,
    TaskOrchestrateRequest,
    TaskOrchestrateResponse,
    ResolveClarificationRequest,
    CreateCollaborationSessionRequest,
    CreateHandoffRequest,
    AcknowledgeHandoffRequest,
    SubmitClarificationRequest,
)
from core.task_logger import create_task_log, get_task_log, list_task_logs, update_task_status
from agents.manager_agent import ManagerAgent
from tasks.orchestrator import TaskOrchestrator
from tasks.models import TaskContext, TaskConstraints
from execution.collaboration.service import CollaborationService
from execution.collaboration.session import HandoffAckStatus, ArtifactReference

router = APIRouter()
logger = logging.getLogger(__name__)

# Global singletons
_orchestrator: Optional[TaskOrchestrator] = None
_collaboration_service: Optional[CollaborationService] = None


def get_orchestrator() -> TaskOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        from teams.registry import TeamRegistry
        from execution.pipelines.registry import PipelineRegistry
        from execution.contracts.registry import ExecutionContractRegistry
        from execution.contracts.catalogue import load_contract_catalogue
        from execution.collaboration.registry import TeamCollaborationContractRegistry
        from execution.collaboration.catalogue import load_collaboration_catalogue
        from teams.seed import seed

        team_reg = TeamRegistry()
        pipeline_reg = PipelineRegistry(team_reg)
        exec_contract_reg = ExecutionContractRegistry()
        collab_contract_reg = TeamCollaborationContractRegistry()

        seed_data = seed()
        for team in seed_data["teams"]:
            team_reg.register(team)
        for pipe in seed_data["pipelines"]:
            pipeline_reg.register(pipe)

        load_contract_catalogue(exec_contract_reg)
        load_collaboration_catalogue(collab_contract_reg)

        _orchestrator = TaskOrchestrator(
            team_registry=team_reg,
            pipeline_registry=pipeline_reg,
            execution_contracts=exec_contract_reg,
            collaboration_contracts=collab_contract_reg,
        )
    return _orchestrator


def get_collaboration_service() -> CollaborationService:
    global _collaboration_service
    if _collaboration_service is None:
        from execution.collaboration.registry import TeamCollaborationContractRegistry
        from execution.collaboration.catalogue import load_collaboration_catalogue

        collab_contract_reg = TeamCollaborationContractRegistry()
        load_collaboration_catalogue(collab_contract_reg)
        _collaboration_service = CollaborationService(collab_contract_reg)
    return _collaboration_service


# ── Phase 10 Task Orchestration Endpoints ─────────────────────────────────

@router.post("/orchestrate", response_model=TaskOrchestrateResponse)
async def orchestrate_task_endpoint(body: TaskOrchestrateRequest):
    """
    Transforms user_input into a validated, versioned TaskPlan (Phase 10).
    Does NOT execute the plan.
    """
    orchestrator = get_orchestrator()
    ctx = TaskContext(**body.context) if body.context else None
    cst = TaskConstraints(**body.constraints) if body.constraints else None

    result = orchestrator.orchestrate_task(
        user_input=body.user_input,
        organization_id=body.organization_id,
        context=ctx,
        constraints=cst,
    )

    plan_data = None
    if result.plan_id:
        plan = orchestrator.get_plan(result.plan_id)
        if plan:
            plan_data = plan.model_dump()

    return TaskOrchestrateResponse(
        task_id=result.task_id,
        plan_id=result.plan_id,
        status=result.status.value if hasattr(result.status, "value") else str(result.status),
        work_unit_count=len(result.work_units),
        required_outputs=result.required_outputs,
        clarifications=[c.model_dump() for c in result.clarifications],
        blockers=[b.model_dump() for b in result.blocking_issues],
        warnings=[w.model_dump() for w in result.warnings],
        plan=plan_data,
    )


@router.get("/{task_id}/plan", summary="Get TaskPlan for task")
async def get_task_plan_endpoint(task_id: str):
    """Retrieve TaskPlan generated for task_id."""
    orchestrator = get_orchestrator()
    task = orchestrator.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")
    if not task.current_plan_id:
        raise HTTPException(status_code=404, detail=f"No plan generated for task '{task_id}'")

    plan = orchestrator.get_plan(task.current_plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail=f"Plan '{task.current_plan_id}' not found")

    return plan.model_dump()


@router.post("/{task_id}/clarification/resolve", response_model=TaskOrchestrateResponse)
async def resolve_clarification_endpoint(task_id: str, body: ResolveClarificationRequest):
    """Resolve a pending TaskClarification and re-orchestrate the task plan."""
    orchestrator = get_orchestrator()
    try:
        result = orchestrator.resolve_clarification(
            task_id=task_id,
            clarification_id=body.clarification_id,
            response_text=body.response_text,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    plan_data = None
    if result.plan_id:
        plan = orchestrator.get_plan(result.plan_id)
        if plan:
            plan_data = plan.model_dump()

    return TaskOrchestrateResponse(
        task_id=result.task_id,
        plan_id=result.plan_id,
        status=result.status.value if hasattr(result.status, "value") else str(result.status),
        work_unit_count=len(result.work_units),
        required_outputs=result.required_outputs,
        clarifications=[c.model_dump() for c in result.clarifications],
        blockers=[b.model_dump() for b in result.blocking_issues],
        warnings=[w.model_dump() for w in result.warnings],
        plan=plan_data,
    )


# ── Phase 11 Multi-Agent Collaboration Endpoints ─────────────────────────

@router.post("/{task_id}/collaborations", summary="Create collaboration session for task work units")
async def create_collaboration_session_endpoint(task_id: str, body: CreateCollaborationSessionRequest):
    """
    Creates a CollaborationSession between source and target WorkUnits.
    Enforces default deny policy via TeamCollaborationContract (TOS 19).
    """
    orchestrator = get_orchestrator()
    collab_service = get_collaboration_service()

    task = orchestrator.get_task(task_id)
    if not task or not task.current_plan_id:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' or TaskPlan not found")

    plan = orchestrator.get_plan(task.current_plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail=f"Plan '{task.current_plan_id}' not found")

    source_wu = next((wu for wu in plan.work_units if wu.work_unit_id == body.source_work_unit_id), None)
    target_wu = next((wu for wu in plan.work_units if wu.work_unit_id == body.target_work_unit_id), None)

    if not source_wu or not target_wu:
        raise HTTPException(status_code=404, detail="Source or target WorkUnit not found in TaskPlan")

    session, error = collab_service.request_collaboration(task_id, source_wu, target_wu)
    if error or not session:
        raise HTTPException(status_code=400, detail=error)

    return session.model_dump()


@router.get("/collaborations/{session_id}", summary="Get collaboration session")
async def get_collaboration_session_endpoint(session_id: str):
    """Retrieve details for a CollaborationSession."""
    collab_service = get_collaboration_service()
    session = collab_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"CollaborationSession '{session_id}' not found")
    return session.model_dump()


@router.post("/collaborations/{session_id}/handoffs", summary="Deliver collaboration handoff")
async def create_handoff_endpoint(session_id: str, body: CreateHandoffRequest):
    """
    Delivers a structured CollaborationHandoff for a session.
    """
    collab_service = get_collaboration_service()
    art_refs = [ArtifactReference(**ref) for ref in body.artifact_references] if body.artifact_references else []

    handoff, error = collab_service.create_and_deliver_handoff(
        session_id=session_id,
        payload=body.payload,
        artifact_references=art_refs,
        summary=body.summary,
    )
    if error and not handoff:
        raise HTTPException(status_code=400, detail=error)

    return handoff.model_dump() if handoff else {"error": error}


@router.post("/collaborations/{session_id}/handoffs/{handoff_id}/ack", summary="Acknowledge collaboration handoff")
async def acknowledge_handoff_endpoint(session_id: str, handoff_id: str, body: AcknowledgeHandoffRequest):
    """
    Acknowledges receipt of handoff (ACCEPTED or REJECTED).
    """
    collab_service = get_collaboration_service()
    ack_status = HandoffAckStatus.ACCEPTED if body.status.upper() == "ACCEPTED" else HandoffAckStatus.REJECTED

    session, error = collab_service.acknowledge_handoff(
        session_id=session_id,
        handoff_id=handoff_id,
        status=ack_status,
        feedback=body.feedback,
    )
    if error or not session:
        raise HTTPException(status_code=400, detail=error)

    return session.model_dump()


@router.post("/collaborations/{session_id}/clarifications", summary="Request structured clarification")
async def request_clarification_endpoint(session_id: str, body: SubmitClarificationRequest):
    """
    Submits a structured clarification request for a collaboration session.
    """
    collab_service = get_collaboration_service()
    clar, error = collab_service.request_clarification(
        session_id=session_id,
        question=body.question,
        required_input=body.required_input,
        reason=body.reason,
    )
    if error or not clar:
        raise HTTPException(status_code=400, detail=error)

    return clar.model_dump()


# ── Legacy Task Endpoints (Preserved for compatibility) ────────────────────

async def _run_project_pipeline(task_id: str, task: str, submitted_by: str):
    """Background coroutine that runs the full manager → team pipeline."""
    try:
        manager = ManagerAgent(task_id=task_id, user_id=submitted_by)
        await manager.run_project(task)
    except Exception as e:
        logger.error(f"Pipeline failed for task {task_id}: {e}")
        await update_task_status(task_id, "failed")


@router.post("/submit", response_model=TaskSubmitResponse, status_code=202)
async def submit_task(body: TaskSubmitRequest):
    """Submit a project task. Legacy endpoint."""
    task_id = await create_task_log(body.task, body.submitted_by)
    asyncio.create_task(_run_project_pipeline(task_id, body.task, body.submitted_by))

    return TaskSubmitResponse(
        task_id=task_id,
        status="queued",
        message="Task sent to Manager Agent. Watch the office come alive! 🏢"
    )


@router.get("/", summary="List recent tasks")
async def list_tasks(limit: int = 20):
    """Return the most recent task logs (newest first)."""
    tasks = await list_task_logs(limit=limit)
    return {"tasks": tasks, "count": len(tasks)}


@router.get("/{task_id}", summary="Get full task log")
async def get_task(task_id: str):
    """Get the complete audit log for a task."""
    log = await get_task_log(task_id)
    if not log:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return log


@router.get("/{task_id}/orchestration", summary="Get orchestration events for a task")
async def get_orchestration_events(task_id: str):
    """
    Return the orchestration phase events for a task.
    Used by the frontend to:
    - Reconnect and catch up on an in-progress orchestration
    - Replay a completed orchestration's timeline
    """
    from core.mongodb import mongodb_connection
    db = mongodb_connection.db
    doc = await db.task_logs.find_one(
        {"task_id": task_id},
        {"orchestration_events": 1, "status": 1, "task_id": 1, "_id": 0},
    )
    if not doc:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return {
        "task_id": task_id,
        "status": doc.get("status", "unknown"),
        "events": doc.get("orchestration_events", []),
    }
