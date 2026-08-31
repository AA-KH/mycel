from fastapi import APIRouter, Depends, HTTPException, status
from organization.schemas import APIResponse

from quality.registry import QualityGateRegistry
from quality.schemas import QualityGateResponse
from api.dependencies.quality import get_quality_gate_registry

router = APIRouter()

@router.get("/quality-gates", response_model=APIResponse)
async def list_quality_gates(
    registry: QualityGateRegistry = Depends(get_quality_gate_registry)
):
    """
    Returns all active Quality Gates.
    """
    gates = await registry.get_all_active()
    return APIResponse(data=[QualityGateResponse(**g.model_dump()).model_dump() for g in gates])

@router.get("/quality-gates/{quality_gate_id}", response_model=APIResponse)
async def get_quality_gate(
    quality_gate_id: str,
    version: str = None,
    registry: QualityGateRegistry = Depends(get_quality_gate_registry)
):
    """
    Returns a specific Quality Gate. Defaults to ACTIVE version if version is omitted.
    """
    gate = await registry.get_gate(quality_gate_id, version)
    if not gate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quality Gate '{quality_gate_id}' not found"
        )
        
    return APIResponse(data=QualityGateResponse(**gate.model_dump()).model_dump())
