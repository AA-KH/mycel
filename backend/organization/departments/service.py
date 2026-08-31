from typing import List
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
