from fastapi import Depends
from api.dependencies.core import DbDep
from api.dependencies.organization import get_team_repository
from organization.registry import TeamRegistry

from execution.reasoning.profiles.repository import (
    TeamReasoningProfileRepository, 
    TeamReasoningStrategyAssignmentRepository
)
from execution.reasoning.profiles.registry import TeamReasoningRegistry
from execution.reasoning.profiles.resolver import TeamReasoningResolver


def get_reasoning_profile_repo(db: DbDep) -> TeamReasoningProfileRepository:
    return TeamReasoningProfileRepository(db)

def get_reasoning_assignment_repo(db: DbDep) -> TeamReasoningStrategyAssignmentRepository:
    return TeamReasoningStrategyAssignmentRepository(db)

def get_team_registry_dep(team_repo = Depends(get_team_repository)) -> TeamRegistry:
    return TeamRegistry(team_repo)

def get_team_reasoning_registry(
    profile_repo: TeamReasoningProfileRepository = Depends(get_reasoning_profile_repo),
    assignment_repo: TeamReasoningStrategyAssignmentRepository = Depends(get_reasoning_assignment_repo),
    team_registry: TeamRegistry = Depends(get_team_registry_dep)
) -> TeamReasoningRegistry:
    return TeamReasoningRegistry(profile_repo, assignment_repo, team_registry)

def get_team_reasoning_resolver(
    registry: TeamReasoningRegistry = Depends(get_team_reasoning_registry)
) -> TeamReasoningResolver:
    return TeamReasoningResolver(registry)
