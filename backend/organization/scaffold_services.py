import os

base_dir = r"d:\Projects\agent-virtual-office\backend\organization"

with open(os.path.join(base_dir, "company", "service.py"), "w", encoding="utf-8") as f:
    f.write('''from datetime import datetime, timezone
from core.errors import DomainError, NotFoundError
from infrastructure.events.schemas import EventEnvelope
from infrastructure.events.base import BaseEventPublisher

from .models import Company
from .schemas import CompanyCreate, CompanyUpdate
from .repository import CompanyRepository
from organization.types import CompanyStatus

class CompanyService:
    def __init__(self, company_repo: CompanyRepository, event_publisher: BaseEventPublisher):
        self.repo = company_repo
        self.publisher = event_publisher

    async def create(self, data: CompanyCreate) -> Company:
        if await self.repo.get_by_slug(data.slug):
            raise DomainError(f"Company with slug '{data.slug}' already exists")
        company = Company(**data.model_dump())
        created = await self.repo.create(company)
        await self._publish("company.created", created.id, created.model_dump())
        return created

    async def get(self, company_id: str) -> Company:
        company = await self.repo.get_by_id(company_id)
        if not company:
            raise NotFoundError(f"Company '{company_id}' not found")
        return company

    async def update(self, company_id: str, data: CompanyUpdate) -> Company:
        company = await self.get(company_id)
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return company
        update_data["updated_at"] = datetime.now(timezone.utc)
        updated = await self.repo.update(company_id, update_data)
        
        await self._publish("company.updated", updated.id, updated.model_dump())
        if data.status == CompanyStatus.ARCHIVED:
            await self._publish("company.archived", updated.id, {})
            
        return updated

    async def _publish(self, event_type: str, entity_id: str, payload: dict):
        event = EventEnvelope(
            event_type=event_type,
            company_id=entity_id,
            payload={"entity_id": entity_id, "data": payload}
        )
        await self.publisher.publish(event)
''')

with open(os.path.join(base_dir, "departments", "service.py"), "w", encoding="utf-8") as f:
    f.write('''from typing import List
from datetime import datetime, timezone
from core.errors import DomainError, NotFoundError
from infrastructure.events.schemas import EventEnvelope
from infrastructure.events.base import BaseEventPublisher

from .models import Department
from .schemas import DepartmentCreate, DepartmentUpdate
from .repository import DepartmentRepository
from organization.company.service import CompanyService
from organization.types import CompanyStatus

class DepartmentService:
    def __init__(self, dept_repo: DepartmentRepository, company_service: CompanyService, event_publisher: BaseEventPublisher):
        self.repo = dept_repo
        self.company_service = company_service
        self.publisher = event_publisher

    async def create(self, company_id: str, data: DepartmentCreate) -> Department:
        company = await self.company_service.get(company_id)
        if company.status == CompanyStatus.ARCHIVED:
            raise DomainError("Cannot create a department in an archived company")
        
        # RULE 7: Cannot become ACTIVE if Company is not ACTIVE
        if data.status == CompanyStatus.ACTIVE and company.status != CompanyStatus.ACTIVE:
            raise DomainError("Cannot create an ACTIVE department because its Company is not ACTIVE")

        if await self.repo.get_by_slug(company_id, data.slug):
            raise DomainError(f"Department with slug '{data.slug}' already exists in this company")

        dept = Department(company_id=company_id, **data.model_dump())
        created = await self.repo.create(dept)
        await self._publish("department.created", created.id, created.model_dump(), company_id)
        return created

    async def get(self, company_id: str, department_id: str) -> Department:
        dept = await self.repo.get_by_id(department_id)
        if not dept or dept.company_id != company_id:
            raise NotFoundError(f"Department '{department_id}' not found in company '{company_id}'")
        return dept

    async def update(self, company_id: str, department_id: str, data: DepartmentUpdate) -> Department:
        dept = await self.get(company_id, department_id)
        
        # RULE 7
        if data.status == CompanyStatus.ACTIVE and dept.status != CompanyStatus.ACTIVE:
            company = await self.company_service.get(company_id)
            if company.status != CompanyStatus.ACTIVE:
                raise DomainError("Cannot activate department because its Company is not ACTIVE")

        # Archive Rule: cannot update archived entity
        if dept.status == CompanyStatus.ARCHIVED and data.status != CompanyStatus.ARCHIVED:
             raise DomainError("Cannot mutate an archived entity")

        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return dept

        update_data["updated_at"] = datetime.now(timezone.utc)
        updated = await self.repo.update(department_id, update_data)
        
        await self._publish("department.updated", updated.id, updated.model_dump(), company_id)
        if data.status == CompanyStatus.ARCHIVED:
            await self._publish("department.archived", updated.id, {}, company_id)

        return updated

    async def list(self, company_id: str) -> List[Department]:
        await self.company_service.get(company_id)
        return await self.repo.get_all_by_company(company_id)

    async def _publish(self, event_type: str, entity_id: str, payload: dict, company_id: str):
        event = EventEnvelope(
            event_type=event_type,
            company_id=company_id,
            payload={"entity_id": entity_id, "data": payload}
        )
        await self.publisher.publish(event)
''')

with open(os.path.join(base_dir, "teams", "service.py"), "w", encoding="utf-8") as f:
    f.write('''from typing import List, Optional
from datetime import datetime, timezone
from core.errors import DomainError, NotFoundError
from infrastructure.events.schemas import EventEnvelope
from infrastructure.events.base import BaseEventPublisher

from .models import Team
from .schemas import TeamCreate, TeamUpdate
from .repository import TeamRepository
from organization.company.service import CompanyService
from organization.departments.service import DepartmentService
from organization.types import CompanyStatus

class TeamService:
    def __init__(self, team_repo: TeamRepository, company_service: CompanyService, dept_service: DepartmentService, event_publisher: BaseEventPublisher):
        self.repo = team_repo
        self.company_service = company_service
        self.dept_service = dept_service
        self.publisher = event_publisher

    async def create(self, company_id: str, data: TeamCreate, department_id: Optional[str] = None) -> Team:
        company = await self.company_service.get(company_id)
        if company.status == CompanyStatus.ARCHIVED:
            raise DomainError("Cannot create a team in an archived company")

        if department_id:
            dept = await self.dept_service.get(company_id, department_id)
            if dept.status == CompanyStatus.ARCHIVED:
                raise DomainError("Cannot create a team in an archived department")
            # RULE 6 variation: Department must be active? The rule says if Team becomes ACTIVE, Company must be ACTIVE.
        
        # RULE 6: Team cannot become ACTIVE if Company not ACTIVE
        if data.status == CompanyStatus.ACTIVE and company.status != CompanyStatus.ACTIVE:
            raise DomainError("Cannot create an ACTIVE team because its Company is not ACTIVE")

        if await self.repo.get_by_slug(company_id, data.slug):
            raise DomainError(f"Team with slug '{data.slug}' already exists in this company")

        team = Team(company_id=company_id, department_id=department_id, **data.model_dump())
        created = await self.repo.create(team)
        await self._publish("team.created", created.id, created.model_dump(), company_id)
        return created

    async def get(self, company_id: str, team_id: str) -> Team:
        team = await self.repo.get_by_id(team_id)
        if not team or team.company_id != company_id:
            raise NotFoundError(f"Team '{team_id}' not found in company '{company_id}'")
        return team

    async def update(self, company_id: str, team_id: str, data: TeamUpdate) -> Team:
        team = await self.get(company_id, team_id)
        
        if team.status == CompanyStatus.ARCHIVED and data.status != CompanyStatus.ARCHIVED:
            raise DomainError("Cannot mutate an archived entity")

        if data.status == CompanyStatus.ACTIVE and team.status != CompanyStatus.ACTIVE:
            company = await self.company_service.get(company_id)
            if company.status != CompanyStatus.ACTIVE:
                raise DomainError("Cannot activate team because its Company is not ACTIVE")

        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return team

        update_data["updated_at"] = datetime.now(timezone.utc)
        updated = await self.repo.update(team_id, update_data)
        
        await self._publish("team.updated", updated.id, updated.model_dump(), company_id)
        if data.status == CompanyStatus.ARCHIVED:
            await self._publish("team.archived", updated.id, {}, company_id)

        return updated

    async def list_by_department(self, company_id: str, department_id: str) -> List[Team]:
        await self.dept_service.get(company_id, department_id)
        return await self.repo.get_all_by_department(company_id, department_id)
        
    async def list_by_company(self, company_id: str) -> List[Team]:
        await self.company_service.get(company_id)
        return await self.repo.get_all_by_company(company_id)

    async def _publish(self, event_type: str, entity_id: str, payload: dict, company_id: str):
        event = EventEnvelope(
            event_type=event_type,
            company_id=company_id,
            payload={"entity_id": entity_id, "data": payload}
        )
        await self.publisher.publish(event)
''')

with open(os.path.join(base_dir, "positions", "service.py"), "w", encoding="utf-8") as f:
    f.write('''from typing import List, Optional
from datetime import datetime, timezone
from core.errors import DomainError, NotFoundError
from infrastructure.events.schemas import EventEnvelope
from infrastructure.events.base import BaseEventPublisher

from .models import Position
from .schemas import PositionCreate, PositionUpdate
from .repository import PositionRepository
from organization.teams.service import TeamService
from organization.types import CompanyStatus

class PositionService:
    def __init__(self, pos_repo: PositionRepository, team_service: TeamService, event_publisher: BaseEventPublisher):
        self.repo = pos_repo
        self.team_service = team_service
        self.publisher = event_publisher

    async def create(self, company_id: str, team_id: str, data: PositionCreate) -> Position:
        team = await self.team_service.get(company_id, team_id)
        if team.status == CompanyStatus.ARCHIVED:
            raise DomainError("Cannot create a position in an archived team")

        # RULE 8: Position cannot become ACTIVE if Team is not ACTIVE (Assuming status == 'open' is ACTIVE)
        if data.status == "open" and team.status != CompanyStatus.ACTIVE:
            raise DomainError("Cannot open a position because its Team is not ACTIVE")

        if await self.repo.get_by_slug(company_id, data.slug):
            raise DomainError(f"Position with slug '{data.slug}' already exists in this company")

        position = Position(
            company_id=company_id, 
            department_id=team.department_id, 
            team_id=team_id, 
            **data.model_dump()
        )
        created = await self.repo.create(position)
        await self._publish("position.created", created.id, created.model_dump(), company_id)
        return created

    async def get(self, company_id: str, position_id: str) -> Position:
        pos = await self.repo.get_by_id(position_id)
        if not pos or pos.company_id != company_id:
            raise NotFoundError(f"Position '{position_id}' not found in company '{company_id}'")
        return pos

    async def update(self, company_id: str, position_id: str, data: PositionUpdate) -> Position:
        pos = await self.get(company_id, position_id)
        
        if pos.status == "archived" and data.status != "archived":
            raise DomainError("Cannot mutate an archived entity")

        if data.status == "open" and pos.status != "open":
            team = await self.team_service.get(company_id, pos.team_id)
            if team.status != CompanyStatus.ACTIVE:
                raise DomainError("Cannot open position because its Team is not ACTIVE")

        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return pos

        update_data["updated_at"] = datetime.now(timezone.utc)
        updated = await self.repo.update(position_id, update_data)
        
        await self._publish("position.updated", updated.id, updated.model_dump(), company_id)
        if data.status == "closed":
            await self._publish("position.closed", updated.id, {}, company_id)
        elif data.status == "open":
            await self._publish("position.opened", updated.id, {}, company_id)

        return updated

    async def list(self, company_id: str, team_id: str) -> List[Position]:
        await self.team_service.get(company_id, team_id)
        return await self.repo.get_all_by_team(company_id, team_id)

    async def _publish(self, event_type: str, entity_id: str, payload: dict, company_id: str):
        event = EventEnvelope(
            event_type=event_type,
            company_id=company_id,
            payload={"entity_id": entity_id, "data": payload}
        )
        await self.publisher.publish(event)
''')

# We'll just leave organization/services.py to re-export OrganizationService so existing code doesn't immediately break.
with open(os.path.join(base_dir, "services.py"), "w", encoding="utf-8") as f:
    f.write('''from typing import List
from organization.company.service import CompanyService
from organization.departments.service import DepartmentService
from organization.teams.service import TeamService
from workforce.positions.service import PositionService
from organization.schemas import OrganizationTreeResponse, TreeCompanyNode, TreeDepartmentNode, TreeTeamNode, TreePositionNode

class OrganizationService:
    def __init__(
        self,
        company_service: CompanyService,
        department_service: DepartmentService,
        team_service: TeamService,
        position_service: PositionService
    ):
        self.company = company_service
        self.department = department_service
        self.team = team_service
        self.position = position_service
        
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
''')
print("Services split.")
