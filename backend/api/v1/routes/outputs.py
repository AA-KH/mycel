from fastapi import APIRouter, Depends, HTTPException, status
from organization.schemas import APIResponse

from outputs.registry import OutputContractRegistry
from outputs.schemas import OutputContractResponse
from api.dependencies.outputs import get_output_contract_registry

router = APIRouter()

@router.get("/output-contracts", response_model=APIResponse)
async def list_output_contracts(
    registry: OutputContractRegistry = Depends(get_output_contract_registry)
):
    """
    Returns all active Output Contracts.
    """
    contracts = await registry.get_all_active()
    return APIResponse(data=[OutputContractResponse(**c.model_dump()).model_dump() for c in contracts])

@router.get("/output-contracts/{output_contract_id}", response_model=APIResponse)
async def get_output_contract(
    output_contract_id: str,
    version: str = None,
    registry: OutputContractRegistry = Depends(get_output_contract_registry)
):
    """
    Returns a specific Output Contract. Defaults to ACTIVE version if version is omitted.
    """
    contract = await registry.get_contract(output_contract_id, version)
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Output Contract '{output_contract_id}' not found"
        )
        
    return APIResponse(data=OutputContractResponse(**contract.model_dump()).model_dump())
