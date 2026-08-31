from typing import List, Optional
from tools.registry import ToolRegistry
from tools.models import ToolDefinition
from .team_repository import TeamToolRepository
from .team_models import TeamToolAssignment, ToolImportance

class TeamToolRegistry:
    def __init__(self, team_tool_repo: TeamToolRepository, global_tool_registry: ToolRegistry):
        self.repo = team_tool_repo
        self.tool_registry = global_tool_registry

    async def get_team_tools(self, team_id: str) -> List[TeamToolAssignment]:
        assignments = await self.repo.get_all_by_team(team_id)
        return [a for a in assignments if a.status == "active"]

    async def get_required_tools(self, team_id: str) -> List[TeamToolAssignment]:
        tools = await self.get_team_tools(team_id)
        return [t for t in tools if t.required]

    async def get_core_tools(self, team_id: str) -> List[TeamToolAssignment]:
        tools = await self.get_team_tools(team_id)
        return [t for t in tools if t.importance == ToolImportance.CORE]

    async def get_optional_tools(self, team_id: str) -> List[TeamToolAssignment]:
        tools = await self.get_team_tools(team_id)
        return [t for t in tools if t.importance == ToolImportance.OPTIONAL]

    async def has_tool(self, team_id: str, tool_id: str) -> bool:
        assignment = await self.repo.get_assignment(team_id, tool_id)
        return bool(assignment and assignment.status == "active")

    async def get_tool_assignment(self, team_id: str, tool_id: str) -> Optional[TeamToolAssignment]:
        assignment = await self.repo.get_assignment(team_id, tool_id)
        if assignment and assignment.status == "active":
            return assignment
        return None
        
    async def resolve_team_tool_definitions(self, team_id: str) -> List[ToolDefinition]:
        """
        Returns the global ToolDefinitions for all tools available to the given team.
        Skips tools that have been disabled globally.
        """
        assignments = await self.get_team_tools(team_id)
        definitions = []
        for a in assignments:
            try:
                definition = self.tool_registry.get_definition(a.tool_id)
                if definition.enabled:
                    definitions.append(definition)
            except Exception:
                continue
        return definitions
