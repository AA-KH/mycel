from typing import List
from organization.company.service import CompanyService
from organization.departments.service import DepartmentService
from organization.teams.service import TeamService
from organization.schemas import OrganizationTreeResponse, TreeCompanyNode, TreeDepartmentNode, TreeTeamNode

class OrganizationService:
    def __init__(
        self,
        company_service: CompanyService,
        department_service: DepartmentService,
        team_service: TeamService
    ):
        self.company = company_service
        self.department = department_service
        self.team = team_service
        
    # Legacy bindings to not break existing tests/code before api migration
    async def create_company(self, *args, **kwargs): return await self.company.create(*args, **kwargs)
    async def get_company(self, *args, **kwargs): return await self.company.get(*args, **kwargs)
    async def update_company(self, *args, **kwargs): return await self.company.update(*args, **kwargs)
    
    async def create_department(self, *args, **kwargs): return await self.department.create(*args, **kwargs)
    async def get_department(self, *args, **kwargs): return await self.department.get(*args, **kwargs)
    async def update_department(self, *args, **kwargs): return await self.department.update(*args, **kwargs)
    async def list_departments(self, *args, **kwargs): return await self.department.list(*args, **kwargs)
    
    # Notice we change how team create works slightly (department_id is now optional in TeamCreate, but wait... 
    # API used: create_team(company_id, department_id, data). We should just wrap it.
    async def create_team(self, company_id, department_id, data): return await self.team.create(company_id, data, department_id)
    async def get_team(self, *args, **kwargs): return await self.team.get(*args, **kwargs)
    async def update_team(self, *args, **kwargs): return await self.team.update(*args, **kwargs)
    async def list_teams(self, *args, **kwargs): return await self.team.list_by_department(*args, **kwargs)
    
    async def create_position(self, *args, **kwargs): return await self.position.create(*args, **kwargs)
    async def get_position(self, *args, **kwargs): return await self.position.get(*args, **kwargs)
    async def update_position(self, *args, **kwargs): return await self.position.update(*args, **kwargs)
    async def list_positions(self, *args, **kwargs): return await self.position.list(*args, **kwargs)

    async def get_organization_tree(self, company_id: str) -> OrganizationTreeResponse:
        company = await self.company.get(company_id)
        departments = await self.department.repo.get_all_by_company(company_id)
        teams = await self.team.repo.get_all_by_company(company_id)
        positions = await self.position.repo.get_all_by_company(company_id)
        # Tree building logic...
        dept_nodes = []
        for dept in departments:
            dept_teams = [t for t in teams if t.department_id == dept.id]
            team_nodes = []
            for team in dept_teams:
                team_positions = [p for p in positions if p.team_id == team.id]
                pos_nodes = [TreePositionNode(id=p.id, title=p.title, slug=p.slug, level=p.level, status=p.status) for p in team_positions]
                team_nodes.append(TreeTeamNode(id=team.id, name=team.name, slug=team.slug, status=team.status, positions=pos_nodes))
            dept_nodes.append(TreeDepartmentNode(id=dept.id, name=dept.name, slug=dept.slug, status=dept.status, teams=team_nodes))
        return OrganizationTreeResponse(
            company=TreeCompanyNode(id=company.id, name=company.name, slug=company.slug, status=company.status),
            departments=dept_nodes
        )
