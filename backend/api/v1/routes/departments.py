from fastapi import APIRouter, Depends, status
from api.dependencies.organization import get_department_service
from organization.departments.service import DepartmentService
from organization.departments.schemas import DepartmentCreate, DepartmentUpdate, DepartmentResponse
from organization.schemas import APIResponse

router = APIRouter()

@router.post("/companies/{company_id}/departments", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create_department(
    company_id: str,
    data: DepartmentCreate,
    service: DepartmentService = Depends(get_department_service)
):
    created = await service.create(company_id, data)
    return APIResponse(data=DepartmentResponse(**created.model_dump()))

@router.get("/companies/{company_id}/departments", response_model=APIResponse)
async def list_departments(
    company_id: str,
    service: DepartmentService = Depends(get_department_service)
):
    departments = await service.list(company_id)
    return APIResponse(data=[DepartmentResponse(**d.model_dump()) for d in departments])

@router.patch("/companies/{company_id}/departments/{department_id}", response_model=APIResponse)
async def update_department(
    company_id: str,
    department_id: str,
    data: DepartmentUpdate,
    service: DepartmentService = Depends(get_department_service)
):
    updated = await service.update(company_id, department_id, data)
    return APIResponse(data=DepartmentResponse(**updated.model_dump()))
