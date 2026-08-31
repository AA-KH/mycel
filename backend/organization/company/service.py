from datetime import datetime, timezone
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
