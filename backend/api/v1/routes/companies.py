from fastapi import APIRouter, Depends, status
from api.dependencies.organization import get_company_service
from organization.company.service import CompanyService
from organization.company.schemas import CompanyCreate, CompanyUpdate, CompanyResponse
from organization.schemas import APIResponse

router = APIRouter()

@router.post("/companies", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create_company(
    data: CompanyCreate,
    service: CompanyService = Depends(get_company_service)
):
    created = await service.create(data)
    return APIResponse(data=CompanyResponse(**created.model_dump()))

@router.get("/companies/{company_id}", response_model=APIResponse)
async def get_company(
    company_id: str,
    service: CompanyService = Depends(get_company_service)
):
    company = await service.get(company_id)
    return APIResponse(data=CompanyResponse(**company.model_dump()))

@router.patch("/companies/{company_id}", response_model=APIResponse)
async def update_company(
    company_id: str,
    data: CompanyUpdate,
    service: CompanyService = Depends(get_company_service)
):
    updated = await service.update(company_id, data)
    return APIResponse(data=CompanyResponse(**updated.model_dump()))

# Note: /companies/{company_id}/organization tree route can live here too, but needs OrganizationService which requires all.
# For simplicity, we import OrganizationService just for that route.
from api.dependencies.organization import get_organization_service
from organization.services import OrganizationService

@router.get("/companies/{company_id}/organization", response_model=APIResponse)
async def get_organization_tree(
    company_id: str,
    service: OrganizationService = Depends(get_organization_service)
):
    tree = await service.get_organization_tree(company_id)
    return APIResponse(data=tree)
