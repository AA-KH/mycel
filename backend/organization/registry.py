from typing import Optional
from core.errors import NotFoundError
from .company.repository import CompanyRepository
from .departments.repository import DepartmentRepository
from .teams.repository import TeamRepository
from .company.models import Company
from .departments.models import Department
from .teams.models import Team


class OrganizationRegistry:
    """Safe identity lookups for the organization domain."""
    
    def __init__(
        self,
        company_repo: CompanyRepository,
        department_repo: DepartmentRepository,
        team_repo: TeamRepository
    ):
        self.company_repo = company_repo
        self.department_repo = department_repo
        self.team_repo = team_repo

    async def get_company(self, company_id: str) -> Company:
        company = await self.company_repo.get_by_id(company_id)
        if not company:
            raise NotFoundError(f"Company '{company_id}' not found")
        return company

    async def get_department(self, department_id: str) -> Department:
        dept = await self.department_repo.get_by_id(department_id)
        if not dept:
            raise NotFoundError(f"Department '{department_id}' not found")
        return dept

    async def get_team(self, team_id: str) -> Team:
        team = await self.team_repo.get_by_id(team_id)
        if not team:
            raise NotFoundError(f"Team '{team_id}' not found")
        return team




class TeamRegistry:
    """Specialized registry for Team discovery."""
    
    def __init__(self, team_repo: TeamRepository):
        self.team_repo = team_repo

    async def resolve_team_identity(self, team_id: str) -> Team:
        team = await self.team_repo.get_by_id(team_id)
        if not team:
            raise NotFoundError(f"Team '{team_id}' not found")
        return team
    
    async def get_active_teams(self, company_id: str) -> list[Team]:
        teams = await self.team_repo.get_all_by_company(company_id)
        return [t for t in teams if t.status == "active"]
