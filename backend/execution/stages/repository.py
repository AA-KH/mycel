from typing import List, Optional
from infrastructure.database.repositories.base import BaseRepository
from .models import StageDefinition, StageDefinitionStatus

class StageDefinitionRepository(BaseRepository[StageDefinition]):
    def __init__(self, db):
        super().__init__(db, "stage_definitions", StageDefinition)

    async def get_by_definition_id(self, stage_definition_id: str, version: Optional[str] = None) -> Optional[StageDefinition]:
        """Returns the specific stage definition. If version is omitted, returns the ACTIVE version."""
        query = {"stage_definition_id": stage_definition_id}
        if version:
            query["version"] = version
        else:
            query["status"] = StageDefinitionStatus.ACTIVE.value
            
        docs = await self.find(query, limit=1)
        return docs[0] if docs else None
        
    async def get_all_active(self) -> List[StageDefinition]:
        return await self.find({"status": StageDefinitionStatus.ACTIVE.value}, limit=100)
