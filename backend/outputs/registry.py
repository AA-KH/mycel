from typing import List, Optional
from core.errors import DomainError

from .repository import OutputContractRepository
from .models import OutputContract
from .validator import OutputContractValidator

class OutputContractRegistry:
    def __init__(self, repository: OutputContractRepository):
        self.repository = repository

    async def get_contract(self, output_contract_id: str, version: Optional[str] = None) -> Optional[OutputContract]:
        return await self.repository.get_by_contract_id(output_contract_id, version)

    async def get_all_active(self) -> List[OutputContract]:
        return await self.repository.get_all_active()

    async def register_contract(self, contract: OutputContract) -> OutputContract:
        # Prevent registering duplicate ID+Version combinations
        existing = await self.get_contract(contract.output_contract_id, contract.version)
        if existing:
            raise DomainError(f"OutputContract '{contract.output_contract_id}' version '{contract.version}' already exists.")
            
        OutputContractValidator.validate_contract(contract)
        return await self.repository.create(contract)
