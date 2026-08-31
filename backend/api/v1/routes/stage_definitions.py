from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from organization.schemas import APIResponse

from execution.stages.registry import StageDefinitionRegistry
from execution.stages.schemas import StageDefinitionResponse
from api.dependencies.definitions import get_stage_definition_registry

router = APIRouter()

@router.get("/stage-definitions", response_model=APIResponse)
async def list_stage_definitions(
    registry: StageDefinitionRegistry = Depends(get_stage_definition_registry)
):
    """
    Returns all active Stage Definitions.
    """
    definitions = await registry.get_all_active()
    return APIResponse(data=[StageDefinitionResponse(**d.model_dump()).model_dump() for d in definitions])

@router.get("/stage-definitions/{definition_id}", response_model=APIResponse)
async def get_stage_definition(
    definition_id: str,
    version: str = None,
    registry: StageDefinitionRegistry = Depends(get_stage_definition_registry)
):
    """
    Returns a specific Stage Definition. Defaults to ACTIVE version if version is omitted.
    """
    definition = await registry.get_definition(definition_id, version)
    if not definition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stage Definition '{definition_id}' not found"
        )
        
    return APIResponse(data=StageDefinitionResponse(**definition.model_dump()).model_dump())
