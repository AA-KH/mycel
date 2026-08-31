"""
Autonomy API Schemas (Phase 16)
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from autonomy.models import (
    ObjectivePriority, AutonomyLevel, SuccessCriteria,
    ObjectiveConstraints, AutonomyBudget, CompanyObjective,
    CompanyPlan, CompanyStateSnapshot, AutonomyDecision,
    AutonomousAction, AutonomyEscalation, AutonomyHealth
)


# ─────────────────────────────────────────────────────────────────────────────
# Objective Requests & Responses
# ─────────────────────────────────────────────────────────────────────────────

class CreateObjectiveRequest(BaseModel):
    organization_id: str
    title: str
    description: str
    priority: ObjectivePriority = ObjectivePriority.MEDIUM
    autonomy_level: AutonomyLevel = AutonomyLevel.SUPERVISED
    success_criteria: List[SuccessCriteria] = Field(default_factory=list)
    constraints: Optional[ObjectiveConstraints] = None
    budget_config: Optional[AutonomyBudget] = None


class ObjectiveResponse(BaseModel):
    objective: CompanyObjective
    progress: float = 0.0
    active_plan_id: Optional[str] = None


class PlanResponse(BaseModel):
    plan: CompanyPlan
    is_active: bool


class ProgressResponse(BaseModel):
    snapshot: CompanyStateSnapshot


class DecisionListResponse(BaseModel):
    decisions: List[AutonomyDecision]


class ActionListResponse(BaseModel):
    actions: List[AutonomousAction]


class EscalationListResponse(BaseModel):
    escalations: List[AutonomyEscalation]


# ─────────────────────────────────────────────────────────────────────────────
# Action / Intervention Requests
# ─────────────────────────────────────────────────────────────────────────────

class ApproveActionRequest(BaseModel):
    approved_by: str
    reason: str = "Approved by user"


class ReplanRequest(BaseModel):
    reason: str
    skip_completed_phases: bool = True


class HealthResponse(BaseModel):
    health: AutonomyHealth
