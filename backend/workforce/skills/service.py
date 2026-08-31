from typing import List
from datetime import datetime, timezone
from core.errors import DomainError, NotFoundError
from infrastructure.events.schemas import EventEnvelope
from infrastructure.events.base import BaseEventPublisher

from .models import Skill, TeamSkillAssignment, SkillStatus, TeamSkillStatus
from .schemas import SkillCreate, SkillUpdate, TeamSkillAssignmentCreate, TeamSkillAssignmentUpdate
from .repository import SkillRepository, TeamSkillRepository
from .validators import validate_proficiency_baseline

# We need to verify if Team exists. We can use the TeamRegistry from organization layer.
from organization.registry import TeamRegistry

class SkillService:
    def __init__(self, skill_repo: SkillRepository, event_publisher: BaseEventPublisher):
        self.repo = skill_repo
        self.publisher = event_publisher

    async def create(self, data: SkillCreate) -> Skill:
        if await self.repo.get_by_skill_id(data.skill_id):
            raise DomainError(f"Skill '{data.skill_id}' already exists")
            
        skill = Skill(**data.model_dump())
        created = await self.repo.create(skill)
        await self._publish("skill.created", created.skill_id, created.model_dump())
        return created

    async def get(self, skill_id: str) -> Skill:
        skill = await self.repo.get_by_skill_id(skill_id)
        if not skill:
            raise NotFoundError(f"Skill '{skill_id}' not found")
        return skill

    async def update(self, skill_id: str, data: SkillUpdate) -> Skill:
        skill = await self.get(skill_id)
        
        if skill.status == SkillStatus.ARCHIVED and data.status != SkillStatus.ARCHIVED:
             raise DomainError("Cannot mutate an archived skill")
             
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return skill
            
        update_data["updated_at"] = datetime.now(timezone.utc)
        updated = await self.repo.update(skill.id, update_data)
        
        await self._publish("skill.updated", skill_id, updated.model_dump())
        if data.status == SkillStatus.DEPRECATED:
            await self._publish("skill.deprecated", skill_id, {})
        return updated
        
    async def list_active(self) -> List[Skill]:
        docs = await self.repo.find({"status": SkillStatus.ACTIVE}, limit=1000)
        return docs

    async def _publish(self, event_type: str, skill_id: str, payload: dict):
        event = EventEnvelope(
            event_type=event_type,
            payload={"skill_id": skill_id, "data": payload}
        )
        await self.publisher.publish(event)


class TeamSkillService:
    def __init__(
        self, 
        team_skill_repo: TeamSkillRepository, 
        skill_service: SkillService,
        team_registry: TeamRegistry,
        event_publisher: BaseEventPublisher
    ):
        self.repo = team_skill_repo
        self.skill_service = skill_service
        self.team_registry = team_registry
        self.publisher = event_publisher

    async def assign_skill(self, team_id: str, data: TeamSkillAssignmentCreate) -> TeamSkillAssignment:
        # 1. Validate team exists
        await self.team_registry.resolve_team_identity(team_id)
        
        # 2. Validate skill exists and is ACTIVE
        skill = await self.skill_service.get(data.skill_id)
        if skill.status != SkillStatus.ACTIVE:
            raise DomainError(f"Cannot assign non-active skill '{data.skill_id}'")
            
        # 3. Validate proficiency bounds
        validate_proficiency_baseline(data.proficiency_baseline)
        
        # 4. Check for duplicates
        existing = await self.repo.get_assignment(team_id, data.skill_id)
        if existing:
            raise DomainError(f"Skill '{data.skill_id}' is already assigned to team '{team_id}'")
            
        assignment = TeamSkillAssignment(
            team_id=team_id,
            **data.model_dump()
        )
        created = await self.repo.create(assignment)
        
        await self._publish("team.skill.added", team_id, data.skill_id, created.model_dump())
        return created

    async def update_assignment(self, team_id: str, skill_id: str, data: TeamSkillAssignmentUpdate) -> TeamSkillAssignment:
        assignment = await self.repo.get_assignment(team_id, skill_id)
        if not assignment:
            raise NotFoundError(f"Skill assignment '{skill_id}' not found for team '{team_id}'")
            
        if data.proficiency_baseline is not None:
            validate_proficiency_baseline(data.proficiency_baseline)
            
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return assignment
            
        update_data["updated_at"] = datetime.now(timezone.utc)
        updated = await self.repo.update(assignment.id, update_data)
        
        await self._publish("team.skill.updated", team_id, skill_id, updated.model_dump())
        return updated
        
    async def remove_assignment(self, team_id: str, skill_id: str):
        """Soft delete/deactivate the assignment."""
        assignment = await self.repo.get_assignment(team_id, skill_id)
        if not assignment:
            raise NotFoundError(f"Skill assignment '{skill_id}' not found for team '{team_id}'")
            
        updated = await self.repo.update(assignment.id, {
            "status": TeamSkillStatus.INACTIVE,
            "updated_at": datetime.now(timezone.utc)
        })
        
        await self._publish("team.skill.removed", team_id, skill_id, updated.model_dump())
        return updated

    async def get_team_skills(self, team_id: str) -> List[TeamSkillAssignment]:
        await self.team_registry.resolve_team_identity(team_id)
        assignments = await self.repo.get_all_by_team(team_id)
        return [a for a in assignments if a.status == TeamSkillStatus.ACTIVE]

    async def _publish(self, event_type: str, team_id: str, skill_id: str, payload: dict):
        event = EventEnvelope(
            event_type=event_type,
            payload={"team_id": team_id, "skill_id": skill_id, "data": payload}
        )
        await self.publisher.publish(event)
