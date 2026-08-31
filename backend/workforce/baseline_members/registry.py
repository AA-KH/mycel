from typing import List, Optional
from core.errors import DomainError
from workforce.baseline_members.models import BaselineMember
from workforce.baseline_members.repository import BaselineMemberRepository

class BaselineMemberRegistry:
    def __init__(self, repository: BaselineMemberRepository):
        self.repository = repository
        self._validators = []
        
    def add_validator(self, validator):
        self._validators.append(validator)

    async def register_baseline(self, member: BaselineMember) -> BaselineMember:
        for validator in self._validators:
            await validator.validate_baseline(member)
            
        try:
            return await self.repository.create(member)
        except ValueError as e:
            raise DomainError(str(e))

    async def get(self, baseline_member_id: str) -> Optional[BaselineMember]:
        return await self.repository.get_by_baseline_id(baseline_member_id)

    async def get_version(self, baseline_member_id: str, version: str) -> Optional[BaselineMember]:
        return await self.repository.get_by_baseline_id(baseline_member_id, version)
        
    async def get_by_team(self, team_id: str) -> List[BaselineMember]:
        return await self.repository.get_by_team(team_id)
        
    async def get_by_position(self, position_id: str) -> List[BaselineMember]:
        return await self.repository.get_by_position(position_id)

    async def get_active(self) -> List[BaselineMember]:
        return await self.repository.get_all_active()

    async def find_by_skill(self, skill_id: str) -> List[BaselineMember]:
        return await self.repository.find({"skills.skill_id": skill_id, "status": "active"})

    async def find_by_tool(self, tool_id: str) -> List[BaselineMember]:
        return await self.repository.find({"tools": tool_id, "status": "active"})

    async def find_by_pipeline(self, pipeline_id: str) -> List[BaselineMember]:
        return await self.repository.find({"pipeline_responsibilities": pipeline_id, "status": "active"})

    async def find_by_output(self, output_id: str) -> List[BaselineMember]:
        return await self.repository.find({"output_responsibilities": output_id, "status": "active"})
