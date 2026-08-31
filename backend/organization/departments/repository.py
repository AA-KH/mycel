from typing import List, Optional
from infrastructure.database.repositories.base import BaseRepository
from .models import Department

class DepartmentRepository(BaseRepository[Department]):
    def __init__(self, db):
        super().__init__(db, "departments", Department)

    async def get_by_slug(self, company_id: str, slug: str) -> Optional[Department]:
        docs = await self.find({"company_id": company_id, "slug": slug}, limit=1)
        return docs[0] if docs else None

    async def get_all_by_company(self, company_id: str) -> List[Department]:
        return await self.find({"company_id": company_id}, limit=1000)
