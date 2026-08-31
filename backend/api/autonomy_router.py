"""
Autonomy Router (Phase 16)
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import List

from autonomy.models import (
    CompanyObjective, ObjectiveStatus, AutonomyLevel, AutonomyHealth
)
from autonomy.schemas import (
    CreateObjectiveRequest, ObjectiveResponse, PlanResponse,
    ProgressResponse, DecisionListResponse, ActionListResponse,
    EscalationListResponse, ApproveActionRequest, ReplanRequest,
    HealthResponse
)
from autonomy.registry import ObjectiveRegistry
from autonomy.autonomy_engine import AutonomyEngine
from autonomy.state_observer import CompanyStateObserver

# In a real app, these would be injected via FastAPI Depends
# For Phase 16, we'll instantiate a global registry and engine for the router.
_registry = ObjectiveRegistry()
_engine = AutonomyEngine(registry=_registry)
_observer = CompanyStateObserver()

router = APIRouter()

def get_registry() -> ObjectiveRegistry:
    return _registry

def get_engine() -> AutonomyEngine:
    return _engine


@router.post("/objectives", response_model=ObjectiveResponse, status_code=status.HTTP_201_CREATED)
async def create_objective(req: CreateObjectiveRequest, engine: AutonomyEngine = Depends(get_engine)):
    from autonomy.models import ObjectiveConstraints, AutonomyBudget
    
    objective = CompanyObjective(
        organization_id=req.organization_id,
        title=req.title,
        description=req.description,
        priority=req.priority,
        autonomy_level=req.autonomy_level,
        success_criteria=req.success_criteria,
        constraints=req.constraints or ObjectiveConstraints(),
        budget_config=req.budget_config or AutonomyBudget(),
    )
    engine.obj_manager.create(objective)
    return ObjectiveResponse(objective=objective)


@router.get("/objectives", response_model=List[ObjectiveResponse])
async def list_objectives(organization_id: str = None, registry: ObjectiveRegistry = Depends(get_registry)):
    objectives = registry.list_objectives(organization_id)
    return [ObjectiveResponse(objective=o) for o in objectives]


@router.get("/objectives/{objective_id}", response_model=ObjectiveResponse)
async def get_objective(objective_id: str, registry: ObjectiveRegistry = Depends(get_registry)):
    obj = registry.get_objective(objective_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Objective not found")
    
    # Calculate current progress
    plan = registry.get_plan(obj.current_plan_id) if obj.current_plan_id else None
    snapshot = _observer.observe(obj, plan, {}, {})
    from autonomy.progress_tracker import ProgressTracker
    progress = ProgressTracker().compute(snapshot)
    
    return ObjectiveResponse(
        objective=obj,
        progress=progress,
        active_plan_id=obj.current_plan_id
    )


@router.post("/objectives/{objective_id}/activate", response_model=ObjectiveResponse)
async def activate_objective(objective_id: str, engine: AutonomyEngine = Depends(get_engine)):
    try:
        obj = engine.activate(objective_id)
        # Trigger an initial advance to start planning
        engine.advance(objective_id, trigger="OBJECTIVE_ACTIVATED")
        return await get_objective(objective_id, engine.registry)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/objectives/{objective_id}/pause", response_model=ObjectiveResponse)
async def pause_objective(objective_id: str, engine: AutonomyEngine = Depends(get_engine)):
    try:
        obj = engine.pause(objective_id)
        return await get_objective(objective_id, engine.registry)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/objectives/{objective_id}/resume", response_model=ObjectiveResponse)
async def resume_objective(objective_id: str, engine: AutonomyEngine = Depends(get_engine)):
    try:
        obj = engine.resume(objective_id)
        engine.advance(objective_id, trigger="OBJECTIVE_RESUMED")
        return await get_objective(objective_id, engine.registry)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/objectives/{objective_id}/cancel", response_model=ObjectiveResponse)
async def cancel_objective(objective_id: str, engine: AutonomyEngine = Depends(get_engine)):
    try:
        obj = engine.cancel(objective_id)
        return await get_objective(objective_id, engine.registry)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/objectives/{objective_id}/plan", response_model=PlanResponse)
async def get_current_plan(objective_id: str, registry: ObjectiveRegistry = Depends(get_registry)):
    obj = registry.get_objective(objective_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Objective not found")
    if not obj.current_plan_id:
        raise HTTPException(status_code=404, detail="No active plan for this objective")
    
    plan = registry.get_plan(obj.current_plan_id)
    return PlanResponse(plan=plan, is_active=True)


@router.get("/objectives/{objective_id}/progress", response_model=ProgressResponse)
async def get_progress(objective_id: str, registry: ObjectiveRegistry = Depends(get_registry)):
    obj = registry.get_objective(objective_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Objective not found")
    
    plan = registry.get_plan(obj.current_plan_id) if obj.current_plan_id else None
    # For a real implementation, these would be fetched from actual systems
    task_states = {}
    quality_results = {}
    escalations = registry.get_escalations(objective_id)
    
    snapshot = _observer.observe(obj, plan, task_states, quality_results, escalations=escalations)
    return ProgressResponse(snapshot=snapshot)


@router.get("/objectives/{objective_id}/decisions", response_model=DecisionListResponse)
async def list_decisions(objective_id: str, registry: ObjectiveRegistry = Depends(get_registry)):
    decisions = registry.get_decisions(objective_id)
    return DecisionListResponse(decisions=decisions)


@router.get("/objectives/{objective_id}/actions", response_model=ActionListResponse)
async def list_actions(objective_id: str, registry: ObjectiveRegistry = Depends(get_registry)):
    actions = registry.get_actions(objective_id)
    return ActionListResponse(actions=actions)


@router.post("/objectives/{objective_id}/approve")
async def approve_action(objective_id: str, action_id: str, req: ApproveActionRequest, engine: AutonomyEngine = Depends(get_engine)):
    """
    Called by a human to approve a pending PENDING action (like a REQUEST_APPROVAL decision).
    In Phase 16, this just updates the action status and triggers the engine to advance.
    """
    from autonomy.models import ActionStatus
    from datetime import datetime, timezone
    
    obj = engine.registry.get_objective(objective_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Objective not found")
    
    actions = engine.registry.get_actions(objective_id)
    action = next((a for a in actions if a.action_id == action_id), None)
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    
    if action.status != ActionStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"Action is not PENDING (status: {action.status})")
        
    engine.registry.update_action_status(action_id, ActionStatus.APPROVED)
    
    # Also find the decision and mark it approved
    decisions = engine.registry.get_decisions(objective_id)
    decision = next((d for d in decisions if d.decision_id == action.decision_id), None)
    if decision:
        decision.approved_by = req.approved_by
        decision.approved_at = datetime.now(timezone.utc)
        
    engine.advance(objective_id, trigger="APPROVAL_RECEIVED")
    return {"status": "approved", "action_id": action_id}


@router.post("/objectives/{objective_id}/replan", response_model=PlanResponse)
async def trigger_replan(objective_id: str, req: ReplanRequest, engine: AutonomyEngine = Depends(get_engine)):
    obj = engine.registry.get_objective(objective_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Objective not found")
    
    current_plan = engine.registry.get_plan(obj.current_plan_id) if obj.current_plan_id else None
    if not current_plan:
        raise HTTPException(status_code=400, detail="No current plan to replan from")
        
    new_plan = engine.executor.replanning_engine.replan(
        objective=obj,
        current_plan=current_plan,
        trigger_reason=req.reason,
        registry=engine.registry,
        skip_completed_phases=req.skip_completed_phases
    )
    engine.obj_manager.attach_plan(objective_id, new_plan.plan_id)
    engine.advance(objective_id, trigger="MANUAL_REPLAN")
    
    return PlanResponse(plan=new_plan, is_active=True)


@router.get("/health", response_model=HealthResponse)
async def get_health(engine: AutonomyEngine = Depends(get_engine)):
    return HealthResponse(health=engine.get_health())


@router.post("/killswitch/enable")
async def enable_killswitch(engine: AutonomyEngine = Depends(get_engine)):
    engine.enable_kill_switch()
    return {"status": "kill_switch_enabled"}


@router.post("/killswitch/disable")
async def disable_killswitch(engine: AutonomyEngine = Depends(get_engine)):
    engine.disable_kill_switch()
    return {"status": "kill_switch_disabled"}
