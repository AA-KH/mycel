from typing import List, Optional
from core.errors import DomainError

from .repository import PositionRepository
from .models import Position

class PositionRegistry:
    def __init__(self, repository: PositionRepository):
        self.repository = repository

    async def get_position(self, position_id: str, version: Optional[str] = None) -> Optional[Position]:
        return await self.repository.get_by_position_id(position_id, version)

    async def get_by_team(self, team_id: str) -> List[Position]:
        return await self.repository.get_by_team(team_id)

    async def get_all_active(self) -> List[Position]:
        return await self.repository.get_all_active()

    async def register_position(self, position: Position, validator=None) -> Position:
        existing = await self.get_position(position.position_id, position.version)
        if existing:
            raise DomainError(f"Position '{position.position_id}' version '{position.version}' already exists.")
            
        if validator:
            await validator.validate_position(position)
            
        return await self.repository.create(position)

    async def get(self, position_id: str) -> Optional[Position]:
        return await self.get_position(position_id)

    async def get_version(self, position_id: str, version: str) -> Optional[Position]:
        return await self.get_position(position_id, version)

    async def get_active(self) -> List[Position]:
        return await self.get_all_active()

    async def find_by_skill(self, skill_id: str) -> List[Position]:
        return await self.repository.find_by_skill(skill_id)

    async def find_by_tool(self, tool_id: str) -> List[Position]:
        return await self.repository.find_by_tool(tool_id)

    async def find_by_pipeline(self, pipeline_id: str) -> List[Position]:
        return await self.repository.find_by_pipeline(pipeline_id)

    async def find_by_stage(self, stage_id: str) -> List[Position]:
        return await self.repository.find_by_stage(stage_id)

    async def find_by_output(self, output_contract_id: str) -> List[Position]:
        return await self.repository.find_by_output(output_contract_id)

    async def find_by_team(self, team_id: str) -> List[Position]:
        return await self.get_by_team(team_id)
