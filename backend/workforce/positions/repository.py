from typing import List, Optional
from infrastructure.database.repositories.base import BaseRepository
from .models import Position, PositionStatus

class PositionRepository(BaseRepository[Position]):
    def __init__(self, db):
        super().__init__(db, "positions", Position)

    async def get_by_position_id(self, position_id: str, version: Optional[str] = None) -> Optional[Position]:
        query = {"position_id": position_id}
        if version:
            query["version"] = version
        else:
            query["status"] = PositionStatus.ACTIVE.value
            
        docs = await self.find(query, limit=1)
        return docs[0] if docs else None
        
    async def get_by_team(self, team_id: str) -> List[Position]:
        return await self.find({"team_id": team_id, "status": PositionStatus.ACTIVE.value}, limit=100)

    async def get_all_active(self) -> List[Position]:
        return await self.find({"status": PositionStatus.ACTIVE.value}, limit=100)

    async def find_by_skill(self, skill_id: str) -> List[Position]:
        return await self.find({"required_skills.skill_id": skill_id, "status": PositionStatus.ACTIVE.value}, limit=100)

    async def find_by_tool(self, tool_id: str) -> List[Position]:
        return await self.find({"required_tools.tool_id": tool_id, "status": PositionStatus.ACTIVE.value}, limit=100)

    async def find_by_pipeline(self, pipeline_id: str) -> List[Position]:
        return await self.find({"pipeline_responsibilities": pipeline_id, "status": PositionStatus.ACTIVE.value}, limit=100)

    async def find_by_stage(self, stage_id: str) -> List[Position]:
        return await self.find({"stage_responsibilities": stage_id, "status": PositionStatus.ACTIVE.value}, limit=100)

    async def find_by_output(self, output_contract_id: str) -> List[Position]:
        return await self.find({"output_responsibilities": output_contract_id, "status": PositionStatus.ACTIVE.value}, limit=100)
