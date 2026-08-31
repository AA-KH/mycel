from typing import Optional
from infrastructure.database.repositories.base import BaseRepository
from .models import Company

class CompanyRepository(BaseRepository[Company]):
    def __init__(self, db):
        super().__init__(db, "companies", Company)

    async def get_by_slug(self, slug: str) -> Optional[Company]:
        docs = await self.find({"slug": slug}, limit=1)
        return docs[0] if docs else None
