from fastapi import APIRouter, Depends, status, HTTPException
from typing import List, Optional
from tools.registry.team_service import TeamToolService
from tools.registry.team_registry import TeamToolRegistry
from tools.registry import ToolRegistry
from core.errors import DomainError
from tools.models import ToolDefinition, ToolNotFoundError
from tools.registry.team_schemas import (
    TeamToolAssignmentCreate, TeamToolAssignmentUpdate, TeamToolAssignmentResponse
)
from organization.schemas import APIResponse
from api.dependencies.tools import (
    get_team_tool_service, get_team_tool_registry, get_global_tool_registry
)

router = APIRouter()

# ---------------------------------------------------------
# Global Tools endpoints (Read-only via ToolRegistry)
# ---------------------------------------------------------

@router.get("/tools", response_model=APIResponse)
async def list_global_tools(
    registry: ToolRegistry = Depends(get_global_tool_registry)
):
    # Global tools are in-memory registered via Python definitions.
    tools = [t.definition for t in registry._tools.values() if t.definition.enabled]
    return APIResponse(data=[t.model_dump() for t in tools])

@router.get("/tools/{tool_id}", response_model=APIResponse)
async def get_global_tool(
    tool_id: str,
    registry: ToolRegistry = Depends(get_global_tool_registry)
):
    try:
        tool_def = registry.get_definition(tool_id)
        return APIResponse(data=tool_def.model_dump())
    except ToolNotFoundError:
        raise HTTPException(status_code=404, detail="Tool not found")


# ---------------------------------------------------------
# Team Tools Assignments
# ---------------------------------------------------------

@router.get("/teams/{team_id}/tools", response_model=APIResponse)
async def get_team_tools(
    team_id: str,
    registry: TeamToolRegistry = Depends(get_team_tool_registry)
):
    assignments = await registry.get_team_tools(team_id)
    return APIResponse(data=[TeamToolAssignmentResponse(**a.model_dump()) for a in assignments])

@router.post("/teams/{team_id}/tools", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def assign_team_tool(
    team_id: str,
    data: TeamToolAssignmentCreate,
    service: TeamToolService = Depends(get_team_tool_service)
):
    created = await service.assign_tool(team_id, data)
    return APIResponse(data=TeamToolAssignmentResponse(**created.model_dump()))

@router.patch("/teams/{team_id}/tools/{tool_id}", response_model=APIResponse)
async def update_team_tool(
    team_id: str,
    tool_id: str,
    data: TeamToolAssignmentUpdate,
    service: TeamToolService = Depends(get_team_tool_service)
):
    updated = await service.update_assignment(team_id, tool_id, data)
    return APIResponse(data=TeamToolAssignmentResponse(**updated.model_dump()))

@router.delete("/teams/{team_id}/tools/{tool_id}", response_model=APIResponse)
async def remove_team_tool(
    team_id: str,
    tool_id: str,
    service: TeamToolService = Depends(get_team_tool_service)
):
    updated = await service.remove_assignment(team_id, tool_id)
    return APIResponse(data=TeamToolAssignmentResponse(**updated.model_dump()))
