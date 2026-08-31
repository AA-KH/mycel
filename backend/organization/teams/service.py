from typing import List, Optional
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
