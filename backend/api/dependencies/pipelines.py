from fastapi import Depends
from api.dependencies.core import DbDep
from api.dependencies.organization import get_team_repository
from organization.registry import TeamRegistry

from execution.pipelines.repository import TeamPipelineRepository, PipelineExecutionRepository
from execution.pipelines.registry import PipelineRegistry


def get_team_pipeline_repo(db: DbDep) -> TeamPipelineRepository:
    return TeamPipelineRepository(db)

def get_pipeline_execution_repo(db: DbDep) -> PipelineExecutionRepository:
    return PipelineExecutionRepository(db)

def get_team_registry_dep(team_repo = Depends(get_team_repository)) -> TeamRegistry:
    return TeamRegistry(team_repo)

# A global registry is typically needed for in-memory, but we instantiate per request here for now.
def get_team_pipeline_registry(
    team_registry: TeamRegistry = Depends(get_team_registry_dep)
) -> PipelineRegistry:
    return PipelineRegistry(team_registry)
