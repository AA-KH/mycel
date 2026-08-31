from typing import List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException

from core.errors import DomainError, NotFoundError
from api.dependencies.employees import get_employee_service

from workforce.employees.schemas import (
    EmployeeCreate,
    EmployeeUpdate,
    EmployeeStatusUpdate,
    EmployeeResponse,
    EmployeeProfileResponse,
)
from workforce.employees.services import EmployeeService
from workforce.employees.models import Employee

router = APIRouter(prefix="/companies/{company_id}/employees", tags=["employees"])


@router.post("", response_model=EmployeeResponse, status_code=201)
async def create_employee(
    company_id: str,
    data: EmployeeCreate,
    employee_service: EmployeeService = Depends(get_employee_service),
):
    if data.company_id != company_id:
        raise HTTPException(status_code=400, detail="Path company_id does not match body company_id")
        
    try:
        emp = await employee_service.create_employee(data)
        return emp
    except DomainError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("", response_model=List[EmployeeResponse])
async def list_employees(
    company_id: str,
    department_id: Optional[str] = None,
    team_id: Optional[str] = None,
    position_id: Optional[str] = None,
    employee_service: EmployeeService = Depends(get_employee_service),
):
    emps = await employee_service.list_employees(
        company_id, 
        department_id=department_id, 
        team_id=team_id, 
        position_id=position_id
    )
    return emps


@router.get("/{employee_id}", response_model=EmployeeResponse)
async def get_employee(
    company_id: str,
    employee_id: str,
    employee_service: EmployeeService = Depends(get_employee_service),
):
    try:
        emp = await employee_service.get_employee(company_id, employee_id)
        return emp
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{employee_id}", response_model=EmployeeResponse)
async def update_employee(
    company_id: str,
    employee_id: str,
    data: EmployeeUpdate,
    employee_service: EmployeeService = Depends(get_employee_service),
):
    try:
        emp = await employee_service.update_employee(company_id, employee_id, data)
        return emp
    except DomainError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{employee_id}/status", response_model=EmployeeResponse)
async def update_employee_status(
    company_id: str,
    employee_id: str,
    data: EmployeeStatusUpdate,
    employee_service: EmployeeService = Depends(get_employee_service),
):
    try:
        emp = await employee_service.update_status(company_id, employee_id, data)
        return emp
    except DomainError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{employee_id}/profile", response_model=EmployeeProfileResponse)
async def get_employee_profile(
    company_id: str,
    employee_id: str,
    employee_service: EmployeeService = Depends(get_employee_service),
):
    """
    Returns a sanitized profile for the Pixel Office / frontend.
    Omits sensitive internal capabilities, hidden reasoning configs, and verbose details.
    """
    try:
        emp = await employee_service.get_employee(company_id, employee_id)
        return EmployeeProfileResponse(
            id=emp.id,
            name=emp.name,
            display_name=emp.display_name,
            title=emp.identity.title,
            summary=emp.identity.summary,
            department_id=emp.department_id,
            team_id=emp.team_id,
            position_id=emp.position_id,
            skills={k: v.level for k, v in emp.skills.items()},
            tools=emp.tools,
            performance_score=emp.performance_summary.overall_score,
            status=emp.status
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
