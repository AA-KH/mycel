from fastapi import Depends
from api.dependencies.core import DbDep

from quality.repository import QualityGateRepository, QualityExecutionRepository
from quality.registry import QualityGateRegistry
from quality.executor import QualityGateExecutor
from quality.checks.registry import QualityCheckRegistry
from quality.checks.artifact import ArtifactExistsCheckExecutor, ArtifactFormatCheckExecutor

def get_quality_gate_repo(db: DbDep) -> QualityGateRepository:
    return QualityGateRepository(db)
    
def get_quality_exec_repo(db: DbDep) -> QualityExecutionRepository:
    return QualityExecutionRepository(db)

def get_quality_gate_registry(
    repo: QualityGateRepository = Depends(get_quality_gate_repo)
) -> QualityGateRegistry:
    return QualityGateRegistry(repo)

def get_quality_check_registry() -> QualityCheckRegistry:
    registry = QualityCheckRegistry()
    registry.register(ArtifactExistsCheckExecutor())
    registry.register(ArtifactFormatCheckExecutor())
    return registry

def get_quality_gate_executor(
    check_registry: QualityCheckRegistry = Depends(get_quality_check_registry)
) -> QualityGateExecutor:
    return QualityGateExecutor(check_registry)
