from typing import List, Optional
from infrastructure.database.repositories.base import BaseRepository
from .models import Skill, TeamSkillAssignment

class SkillRepository(BaseRepository[Skill]):
    def __init__(self, db):
        super().__init__(db, "skills", Skill)

    async def get_by_skill_id(self, skill_id: str) -> Optional[Skill]:
        docs = await self.find({"skill_id": skill_id}, limit=1)
        return docs[0] if docs else None
        
    async def get_all_by_domain(self, domain: str) -> List[Skill]:
        return await self.find({"domain": domain}, limit=1000)
        
    async def get_all_by_category(self, category: str) -> List[Skill]:
        return await self.find({"category": category}, limit=1000)


class TeamSkillRepository(BaseRepository[TeamSkillAssignment]):
    def __init__(self, db):
        super().__init__(db, "team_skills", TeamSkillAssignment)

    async def get_assignment(self, team_id: str, skill_id: str) -> Optional[TeamSkillAssignment]:
        docs = await self.find({"team_id": team_id, "skill_id": skill_id}, limit=1)
        return docs[0] if docs else None

    async def get_all_by_team(self, team_id: str) -> List[TeamSkillAssignment]:
        return await self.find({"team_id": team_id}, limit=1000)
