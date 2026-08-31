from fastapi import Depends

from core.mongodb import mongodb_connection
from infrastructure.events.publisher import event_publisher

from organization.repositories import (
    CompanyRepository,
    DepartmentRepository,
    TeamRepository,
    PositionRepository,
)
from organization.services import OrganizationService

from workforce.employees.repositories import EmployeeRepository
from workforce.employees.services import EmployeeService
from workforce.employees.registry import EmployeeRegistry


def get_employee_repository() -> EmployeeRepository:
    return EmployeeRepository(mongodb_connection.db)


def get_employee_service(
    employee_repo: EmployeeRepository = Depends(get_employee_repository),
) -> EmployeeService:
    # Need to construct the org service dependencies
    db = mongodb_connection.db
    org_service = OrganizationService(
        company_repo=CompanyRepository(db),
        dept_repo=DepartmentRepository(db),
        team_repo=TeamRepository(db),
        position_repo=PositionRepository(db),
        event_publisher=event_publisher
    )
    
    return EmployeeService(
        employee_repo=employee_repo,
        organization_service=org_service,
        event_publisher=event_publisher
    )


def get_employee_registry(
    employee_repo: EmployeeRepository = Depends(get_employee_repository),
) -> EmployeeRegistry:
    return EmployeeRegistry(employee_repo)
