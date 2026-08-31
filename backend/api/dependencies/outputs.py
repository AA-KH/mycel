from fastapi import Depends
from api.dependencies.core import DbDep

from outputs.repository import OutputContractRepository
from outputs.registry import OutputContractRegistry
from outputs.resolver import OutputContractResolver

def get_output_contract_repo(db: DbDep) -> OutputContractRepository:
    return OutputContractRepository(db)

def get_output_contract_registry(
    repo: OutputContractRepository = Depends(get_output_contract_repo)
) -> OutputContractRegistry:
    return OutputContractRegistry(repo)

def get_output_contract_resolver(
    registry: OutputContractRegistry = Depends(get_output_contract_registry)
) -> OutputContractResolver:
    return OutputContractResolver(registry)
