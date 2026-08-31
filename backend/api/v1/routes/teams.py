from typing import Optional
from fastapi import APIRouter, Depends, status, Query
from api.dependencies.organization import get_team_service
from organization.teams.service import TeamService
from organization.teams.schemas import TeamCreate, TeamUpdate, TeamResponse
from organization.schemas import APIResponse

router = APIRouter()

@router.post("/companies/{company_id}/teams", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create_team(
    company_id: str,
    data: TeamCreate,
    department_id: Optional[str] = Query(None, description="Optional Department ID"),
    service: TeamService = Depends(get_team_service)
):
    created = await service.create(company_id, data, department_id=department_id)
    return APIResponse(data=TeamResponse(**created.model_dump()))

@router.get("/companies/{company_id}/teams", response_model=APIResponse)
async def list_teams(
    company_id: str,
    department_id: Optional[str] = Query(None, description="Filter by department"),
    service: TeamService = Depends(get_team_service)
):
    if department_id:
        teams = await service.list_by_department(company_id, department_id)
    else:
        teams = await service.list_by_company(company_id)
    return APIResponse(data=[TeamResponse(**t.model_dump()) for t in teams])

@router.patch("/companies/{company_id}/teams/{team_id}", response_model=APIResponse)
async def update_team(
    company_id: str,
    team_id: str,
    data: TeamUpdate,
    service: TeamService = Depends(get_team_service)
):
    updated = await service.update(company_id, team_id, data)
    return APIResponse(data=TeamResponse(**updated.model_dump()))

# For backwards compatibility with the exact route in prompt if needed:
@router.post("/companies/{company_id}/departments/{department_id}/teams", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create_team_in_department(
    company_id: str,
    department_id: str,
    data: TeamCreate,
    service: TeamService = Depends(get_team_service)
):
    created = await service.create(company_id, data, department_id=department_id)
    return APIResponse(data=TeamResponse(**created.model_dump()))

@router.get("/companies/{company_id}/departments/{department_id}/teams", response_model=APIResponse)
async def list_teams_in_department(
    company_id: str,
    department_id: str,
    service: TeamService = Depends(get_team_service)
):
    teams = await service.list_by_department(company_id, department_id)
    return APIResponse(data=[TeamResponse(**t.model_dump()) for t in teams])
