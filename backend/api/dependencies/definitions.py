from fastapi import Depends
from api.dependencies.core import DbDep
from execution.stages.repository import StageDefinitionRepository
from execution.stages.registry import StageDefinitionRegistry

def get_stage_definition_repo(db: DbDep) -> StageDefinitionRepository:
    return StageDefinitionRepository(db)

def get_stage_definition_registry(
    repo: StageDefinitionRepository = Depends(get_stage_definition_repo)
) -> StageDefinitionRegistry:
    return StageDefinitionRegistry(repo)
