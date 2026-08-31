from typing import Optional, List
from core.errors import DomainError

from organization.registry import TeamRegistry
from .repository import TeamReasoningProfileRepository, TeamReasoningStrategyAssignmentRepository
from .models import TeamReasoningProfile, TeamReasoningStrategyAssignment


class TeamReasoningRegistry:
    def __init__(
        self,
        profile_repo: TeamReasoningProfileRepository,
        assignment_repo: TeamReasoningStrategyAssignmentRepository,
        team_registry: TeamRegistry
    ):
        self.profile_repo = profile_repo
        self.assignment_repo = assignment_repo
        self.team_registry = team_registry

    async def get_active_profile(self, team_id: str) -> Optional[TeamReasoningProfile]:
        return await self.profile_repo.get_active_by_team(team_id)

    async def create_profile(
        self, 
        team_id: str, 
        name: str, 
        display_name: str, 
        description: str,
        principles: List[str],
        policies: dict
    ) -> TeamReasoningProfile:
        # Validate team exists
        await self.team_registry.resolve_team_identity(team_id)
        
        # Enforce uniqueness: Only one active profile per team
        existing = await self.get_active_profile(team_id)
        if existing:
            raise DomainError(f"Team '{team_id}' already has an active reasoning profile.")
            
        profile = TeamReasoningProfile(
            team_id=team_id,
            name=name,
            display_name=display_name,
            description=description,
            principles=principles,
            policies=policies
        )
        return await self.profile_repo.create(profile)
        
    async def get_strategy_assignments(self, profile_id: str) -> List[TeamReasoningStrategyAssignment]:
        return await self.assignment_repo.get_by_profile(profile_id)
        
    async def assign_strategy(self, profile_id: str, strategy_id: str, priority: int = 0) -> TeamReasoningStrategyAssignment:
        assignment = TeamReasoningStrategyAssignment(
            reasoning_profile_id=profile_id,
            strategy_id=strategy_id,
            priority=priority
        )
        return await self.assignment_repo.create(assignment)
