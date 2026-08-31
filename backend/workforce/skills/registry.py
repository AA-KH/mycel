from typing import List, Optional
from core.errors import NotFoundError
from .repository import SkillRepository, TeamSkillRepository
from .models import Skill, TeamSkillAssignment, SkillImportance, SkillStatus

class SkillRegistry:
    def __init__(self, skill_repo: SkillRepository):
        self.skill_repo = skill_repo

    async def get_skill(self, skill_id: str) -> Skill:
        skill = await self.skill_repo.get_by_skill_id(skill_id)
        if not skill:
            raise NotFoundError(f"Skill '{skill_id}' not found")
        return skill

    async def get_active_skills(self) -> List[Skill]:
        return await self.skill_repo.find({"status": SkillStatus.ACTIVE}, limit=1000)

    async def find_by_domain(self, domain: str) -> List[Skill]:
        return await self.skill_repo.get_all_by_domain(domain)

    async def find_by_category(self, category: str) -> List[Skill]:
        return await self.skill_repo.get_all_by_category(category)

    async def validate_skill(self, skill_id: str) -> bool:
        skill = await self.skill_repo.get_by_skill_id(skill_id)
        return bool(skill and skill.status == SkillStatus.ACTIVE)


class TeamSkillRegistry:
    def __init__(self, team_skill_repo: TeamSkillRepository):
        self.repo = team_skill_repo

    async def get_team_skills(self, team_id: str) -> List[TeamSkillAssignment]:
        assignments = await self.repo.get_all_by_team(team_id)
        return [a for a in assignments if a.status == "active"]

    async def get_required_skills(self, team_id: str) -> List[TeamSkillAssignment]:
        skills = await self.get_team_skills(team_id)
        return [s for s in skills if s.required]

    async def get_core_skills(self, team_id: str) -> List[TeamSkillAssignment]:
        skills = await self.get_team_skills(team_id)
        return [s for s in skills if s.importance == SkillImportance.CORE]

    async def get_optional_skills(self, team_id: str) -> List[TeamSkillAssignment]:
        skills = await self.get_team_skills(team_id)
        return [s for s in skills if s.importance == SkillImportance.OPTIONAL]

    async def has_skill(self, team_id: str, skill_id: str) -> bool:
        assignment = await self.repo.get_assignment(team_id, skill_id)
        return bool(assignment and assignment.status == "active")

    async def get_skill_baseline(self, team_id: str, skill_id: str) -> Optional[int]:
        assignment = await self.repo.get_assignment(team_id, skill_id)
        if assignment and assignment.status == "active":
            return assignment.proficiency_baseline
        return None
