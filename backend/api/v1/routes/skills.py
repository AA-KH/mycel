from fastapi import APIRouter, Depends, status
from typing import List, Optional
from workforce.skills.service import SkillService, TeamSkillService
from workforce.skills.registry import SkillRegistry, TeamSkillRegistry
from workforce.skills.schemas import (
    SkillCreate, SkillUpdate, SkillResponse,
    TeamSkillAssignmentCreate, TeamSkillAssignmentUpdate, TeamSkillAssignmentResponse
)
from organization.schemas import APIResponse
from api.dependencies.skills import (
    get_skill_service, get_team_skill_service, 
    get_skill_registry, get_team_skill_registry
)

router = APIRouter()

# ---------------------------------------------------------
# Global Skills endpoints
# ---------------------------------------------------------

@router.post("/skills", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create_skill(
    data: SkillCreate,
    service: SkillService = Depends(get_skill_service)
):
    created = await service.create(data)
    return APIResponse(data=SkillResponse(**created.model_dump()))

@router.get("/skills", response_model=APIResponse)
async def list_skills(
    domain: Optional[str] = None,
    category: Optional[str] = None,
    registry: SkillRegistry = Depends(get_skill_registry)
):
    if domain:
        skills = await registry.find_by_domain(domain)
    elif category:
        skills = await registry.find_by_category(category)
    else:
        skills = await registry.get_active_skills()
    
    return APIResponse(data=[SkillResponse(**s.model_dump()) for s in skills])

@router.get("/skills/{skill_id}", response_model=APIResponse)
async def get_skill(
    skill_id: str,
    registry: SkillRegistry = Depends(get_skill_registry)
):
    skill = await registry.get_skill(skill_id)
    return APIResponse(data=SkillResponse(**skill.model_dump()))

@router.patch("/skills/{skill_id}", response_model=APIResponse)
async def update_skill(
    skill_id: str,
    data: SkillUpdate,
    service: SkillService = Depends(get_skill_service)
):
    updated = await service.update(skill_id, data)
    return APIResponse(data=SkillResponse(**updated.model_dump()))


# ---------------------------------------------------------
# Team Skills Assignments
# ---------------------------------------------------------

@router.get("/teams/{team_id}/skills", response_model=APIResponse)
async def get_team_skills(
    team_id: str,
    registry: TeamSkillRegistry = Depends(get_team_skill_registry)
):
    assignments = await registry.get_team_skills(team_id)
    return APIResponse(data=[TeamSkillAssignmentResponse(**a.model_dump()) for a in assignments])

@router.post("/teams/{team_id}/skills", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def assign_team_skill(
    team_id: str,
    data: TeamSkillAssignmentCreate,
    service: TeamSkillService = Depends(get_team_skill_service)
):
    created = await service.assign_skill(team_id, data)
    return APIResponse(data=TeamSkillAssignmentResponse(**created.model_dump()))

@router.patch("/teams/{team_id}/skills/{skill_id}", response_model=APIResponse)
async def update_team_skill(
    team_id: str,
    skill_id: str,
    data: TeamSkillAssignmentUpdate,
    service: TeamSkillService = Depends(get_team_skill_service)
):
    updated = await service.update_assignment(team_id, skill_id, data)
    return APIResponse(data=TeamSkillAssignmentResponse(**updated.model_dump()))

@router.delete("/teams/{team_id}/skills/{skill_id}", response_model=APIResponse)
async def remove_team_skill(
    team_id: str,
    skill_id: str,
    service: TeamSkillService = Depends(get_team_skill_service)
):
    updated = await service.remove_assignment(team_id, skill_id)
    return APIResponse(data=TeamSkillAssignmentResponse(**updated.model_dump()))
