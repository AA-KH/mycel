from typing import List, Optional
from infrastructure.database.repositories.base import BaseRepository
from .team_models import TeamToolAssignment

class TeamToolRepository(BaseRepository[TeamToolAssignment]):
    def __init__(self, db):
        super().__init__(db, "team_tools", TeamToolAssignment)

    async def get_assignment(self, team_id: str, tool_id: str) -> Optional[TeamToolAssignment]:
        docs = await self.find({"team_id": team_id, "tool_id": tool_id}, limit=1)
        return docs[0] if docs else None

    async def get_all_by_team(self, team_id: str) -> List[TeamToolAssignment]:
        return await self.find({"team_id": team_id}, limit=1000)
