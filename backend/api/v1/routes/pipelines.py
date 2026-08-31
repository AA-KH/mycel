from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from organization.schemas import APIResponse

from execution.pipelines.registry import PipelineRegistry
from execution.pipelines.schemas import TeamPipelineResponse
from api.dependencies.pipelines import get_team_pipeline_registry

router = APIRouter()

@router.get("/teams/{team_id}/pipelines", response_model=APIResponse)
async def get_team_pipelines(
    team_id: str,
    registry: PipelineRegistry = Depends(get_team_pipeline_registry)
):
    """
    Returns all active pipelines for a team.
    """
    pipelines = registry.get_team_pipelines(team_id)
    return APIResponse(data=[TeamPipelineResponse(**p.model_dump()).model_dump() for p in pipelines])

@router.get("/teams/{team_id}/pipelines/{pipeline_id}", response_model=APIResponse)
async def get_team_pipeline(
    team_id: str,
    pipeline_id: str,
    registry: PipelineRegistry = Depends(get_team_pipeline_registry)
):
    """
    Returns a specific active pipeline for a team.
    """
    pipeline = registry.get_pipeline(pipeline_id)
    if not pipeline or pipeline.team_id != team_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pipeline '{pipeline_id}' not found for team '{team_id}'"
        )
        
    return APIResponse(data=TeamPipelineResponse(**pipeline.model_dump()).model_dump())
