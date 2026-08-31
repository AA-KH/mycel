from typing import List, Optional
from infrastructure.database.repositories.base import BaseRepository
from .models import Team

class TeamRepository(BaseRepository[Team]):
    def __init__(self, db):
        super().__init__(db, "teams", Team)

    async def get_by_slug(self, company_id: str, slug: str) -> Optional[Team]:
        docs = await self.find({"company_id": company_id, "slug": slug}, limit=1)
        return docs[0] if docs else None

    async def get_all_by_company(self, company_id: str) -> List[Team]:
        return await self.find({"company_id": company_id}, limit=1000)

    async def get_all_by_department(self, company_id: str, department_id: str) -> List[Team]:
        return await self.find({"company_id": company_id, "department_id": department_id}, limit=1000)
