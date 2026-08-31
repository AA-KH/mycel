from fastapi import Depends
from api.dependencies.core import DbDep, EventPublisherDep
from api.dependencies.organization import get_team_repository

from tools.registry import ToolRegistry, registry as global_tool_registry
from tools.registry.team_repository import TeamToolRepository
from tools.registry.team_service import TeamToolService
from tools.registry.team_registry import TeamToolRegistry
from organization.registry import TeamRegistry

def get_team_tool_repository(db: DbDep) -> TeamToolRepository:
    return TeamToolRepository(db)

def get_global_tool_registry() -> ToolRegistry:
    return global_tool_registry

def get_team_registry_dep(
    team_repo = Depends(get_team_repository)
) -> TeamRegistry:
    return TeamRegistry(team_repo)

def get_team_tool_service(
    publisher: EventPublisherDep,
    team_tool_repo: TeamToolRepository = Depends(get_team_tool_repository),
    tool_registry: ToolRegistry = Depends(get_global_tool_registry),
    team_registry: TeamRegistry = Depends(get_team_registry_dep)
) -> TeamToolService:
    return TeamToolService(team_tool_repo, tool_registry, team_registry, publisher)

def get_team_tool_registry(
    repo: TeamToolRepository = Depends(get_team_tool_repository),
    tool_registry: ToolRegistry = Depends(get_global_tool_registry)
) -> TeamToolRegistry:
    return TeamToolRegistry(repo, tool_registry)
