"""
Organization service dependencies.
Provides repository and service instantiation for endpoints.
"""

from fastapi import Depends
from api.dependencies.core import DbDep, EventPublisherDep
from organization.repositories import CompanyRepository, DepartmentRepository, TeamRepository
from organization.services import OrganizationService

def get_company_repository(db: DbDep) -> CompanyRepository:
    return CompanyRepository(db)

def get_department_repository(db: DbDep) -> DepartmentRepository:
    return DepartmentRepository(db)

def get_team_repository(db: DbDep) -> TeamRepository:
    return TeamRepository(db)

from organization.company.service import CompanyService
from organization.departments.service import DepartmentService
from organization.teams.service import TeamService

def get_company_service(
    publisher: EventPublisherDep,
    repo: CompanyRepository = Depends(get_company_repository)
) -> CompanyService:
    return CompanyService(repo, publisher)

def get_department_service(
    publisher: EventPublisherDep,
    repo: DepartmentRepository = Depends(get_department_repository),
    company_service: CompanyService = Depends(get_company_service)
) -> DepartmentService:
    return DepartmentService(repo, company_service, publisher)

def get_team_service(
    publisher: EventPublisherDep,
    repo: TeamRepository = Depends(get_team_repository),
    company_service: CompanyService = Depends(get_company_service),
    dept_service: DepartmentService = Depends(get_department_service)
) -> TeamService:
    return TeamService(repo, company_service, dept_service, publisher)

def get_organization_service(
    company_service: CompanyService = Depends(get_company_service),
    department_service: DepartmentService = Depends(get_department_service),
    team_service: TeamService = Depends(get_team_service)
) -> OrganizationService:
    return OrganizationService(
        company_service=company_service,
        department_service=department_service,
        team_service=team_service
    )
