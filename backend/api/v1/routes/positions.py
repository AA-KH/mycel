from fastapi import APIRouter, Depends, HTTPException, status
from organization.schemas import APIResponse

from workforce.positions.registry import PositionRegistry
from workforce.positions.schemas import PositionResponse
from api.dependencies.workforce import get_position_registry

router = APIRouter()

@router.get("/positions", response_model=APIResponse)
async def list_positions(
    registry: PositionRegistry = Depends(get_position_registry)
):
    """
    Returns all active Positions.
    """
    positions = await registry.get_all_active()
    return APIResponse(data=[PositionResponse(**p.model_dump()).model_dump() for p in positions])

@router.get("/positions/{position_id}", response_model=APIResponse)
async def get_position(
    position_id: str,
    version: str = None,
    registry: PositionRegistry = Depends(get_position_registry)
):
    """
    Returns a specific Position. Defaults to ACTIVE version if version is omitted.
    """
    pos = await registry.get_position(position_id, version)
    if not pos:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Position '{position_id}' not found"
        )
        
    return APIResponse(data=PositionResponse(**pos.model_dump()).model_dump())

@router.get("/teams/{team_id}/positions", response_model=APIResponse)
async def list_team_positions(
    team_id: str,
    registry: PositionRegistry = Depends(get_position_registry)
):
    """
    Returns all active Positions for a team.
    """
    positions = await registry.get_by_team(team_id)
    return APIResponse(data=[PositionResponse(**p.model_dump()).model_dump() for p in positions])
