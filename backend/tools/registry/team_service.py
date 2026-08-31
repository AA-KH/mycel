from typing import List
from datetime import datetime, timezone
from core.errors import DomainError, NotFoundError
from infrastructure.events.schemas import EventEnvelope
from infrastructure.events.base import BaseEventPublisher

from tools.registry import ToolRegistry
from tools.models import ToolNotFoundError
from organization.registry import TeamRegistry

from .team_models import TeamToolAssignment, TeamToolStatus
from .team_schemas import TeamToolAssignmentCreate, TeamToolAssignmentUpdate
from .team_repository import TeamToolRepository


class TeamToolService:
    def __init__(
        self, 
        team_tool_repo: TeamToolRepository, 
        global_tool_registry: ToolRegistry,
        team_registry: TeamRegistry,
        event_publisher: BaseEventPublisher
    ):
        self.repo = team_tool_repo
        self.tool_registry = global_tool_registry
        self.team_registry = team_registry
        self.publisher = event_publisher

    async def assign_tool(self, team_id: str, data: TeamToolAssignmentCreate) -> TeamToolAssignment:
        # 1. Validate team exists
        await self.team_registry.resolve_team_identity(team_id)
        
        # 2. Validate tool exists in global registry and is enabled
        try:
            tool_def = self.tool_registry.get_definition(data.tool_id)
            if not tool_def.enabled:
                raise DomainError(f"Cannot assign disabled tool '{data.tool_id}'")
        except ToolNotFoundError:
            raise DomainError(f"Tool '{data.tool_id}' does not exist in the global registry")
            
        # 3. Check for duplicates
        existing = await self.repo.get_assignment(team_id, data.tool_id)
        if existing:
            raise DomainError(f"Tool '{data.tool_id}' is already assigned to team '{team_id}'")
            
        assignment = TeamToolAssignment(
            team_id=team_id,
            **data.model_dump()
        )
        created = await self.repo.create(assignment)
        
        await self._publish("team.tool.added", team_id, data.tool_id, created.model_dump())
        return created

    async def update_assignment(self, team_id: str, tool_id: str, data: TeamToolAssignmentUpdate) -> TeamToolAssignment:
        assignment = await self.repo.get_assignment(team_id, tool_id)
        if not assignment:
            raise NotFoundError(f"Tool assignment '{tool_id}' not found for team '{team_id}'")
            
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return assignment
            
        update_data["updated_at"] = datetime.now(timezone.utc)
        updated = await self.repo.update(assignment.id, update_data)
        
        await self._publish("team.tool.updated", team_id, tool_id, updated.model_dump())
        return updated
        
    async def remove_assignment(self, team_id: str, tool_id: str):
        """Soft delete/deactivate the assignment."""
        assignment = await self.repo.get_assignment(team_id, tool_id)
        if not assignment:
            raise NotFoundError(f"Tool assignment '{tool_id}' not found for team '{team_id}'")
            
        updated = await self.repo.update(assignment.id, {
            "status": TeamToolStatus.INACTIVE,
            "updated_at": datetime.now(timezone.utc)
        })
        
        await self._publish("team.tool.removed", team_id, tool_id, updated.model_dump())
        return updated

    async def get_team_tools(self, team_id: str) -> List[TeamToolAssignment]:
        await self.team_registry.resolve_team_identity(team_id)
        assignments = await self.repo.get_all_by_team(team_id)
        return [a for a in assignments if a.status == TeamToolStatus.ACTIVE]

    async def _publish(self, event_type: str, team_id: str, tool_id: str, payload: dict):
        event = EventEnvelope(
            event_type=event_type,
            payload={"team_id": team_id, "tool_id": tool_id, "data": payload}
        )
        await self.publisher.publish(event)
