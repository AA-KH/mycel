from typing import List, Optional
from infrastructure.database.repositories.base import BaseRepository
from .models import TeamReasoningProfile, TeamReasoningStrategyAssignment

class TeamReasoningProfileRepository(BaseRepository[TeamReasoningProfile]):
    def __init__(self, db):
        super().__init__(db, "team_reasoning_profiles", TeamReasoningProfile)

    async def get_active_by_team(self, team_id: str) -> Optional[TeamReasoningProfile]:
        """Returns the single active reasoning profile for a team."""
        docs = await self.find({"team_id": team_id, "status": "active"}, limit=1)
        return docs[0] if docs else None


class TeamReasoningStrategyAssignmentRepository(BaseRepository[TeamReasoningStrategyAssignment]):
    def __init__(self, db):
        super().__init__(db, "team_reasoning_assignments", TeamReasoningStrategyAssignment)

    async def get_by_profile(self, profile_id: str) -> List[TeamReasoningStrategyAssignment]:
        """Returns all strategy assignments for a specific reasoning profile."""
        return await self.find({"reasoning_profile_id": profile_id, "status": "active"}, limit=100)
