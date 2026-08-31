from fastapi import APIRouter, Depends, HTTPException, status
from organization.schemas import APIResponse

from execution.reasoning.profiles.resolver import TeamReasoningResolver
from api.dependencies.reasoning import get_team_reasoning_resolver

router = APIRouter()

@router.get("/teams/{team_id}/reasoning", response_model=APIResponse)
async def get_team_reasoning_philosophy(
    team_id: str,
    resolver: TeamReasoningResolver = Depends(get_team_reasoning_resolver)
):
    """
    Returns the resolved reasoning philosophy (profile + strategies) for a team.
    """
    resolved = await resolver.resolve(team_id)
    if not resolved:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active reasoning philosophy found for team '{team_id}'"
        )
        
    return APIResponse(data=resolved.model_dump())
