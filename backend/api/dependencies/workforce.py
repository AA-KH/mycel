from fastapi import Depends
from api.dependencies.core import DbDep

from workforce.positions.repository import PositionRepository
from workforce.positions.registry import PositionRegistry
from workforce.positions.resolver import PositionCapabilityResolver
from api.dependencies.organization import get_team_repository

def get_position_repo(db: DbDep) -> PositionRepository:
    return PositionRepository(db)

def get_position_registry(
    repo: PositionRepository = Depends(get_position_repo)
) -> PositionRegistry:
    return PositionRegistry(repo)

def get_position_resolver(
    team_repo = Depends(get_team_repository)
) -> PositionCapabilityResolver:
    return PositionCapabilityResolver(team_repo)
