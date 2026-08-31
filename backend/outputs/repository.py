from typing import List, Optional
from infrastructure.database.repositories.base import BaseRepository
from .models import OutputContract, OutputContractStatus

class OutputContractRepository(BaseRepository[OutputContract]):
    def __init__(self, db):
        super().__init__(db, "output_contracts", OutputContract)

    async def get_by_contract_id(self, output_contract_id: str, version: Optional[str] = None) -> Optional[OutputContract]:
        query = {"output_contract_id": output_contract_id}
        if version:
            query["version"] = version
        else:
            query["status"] = OutputContractStatus.ACTIVE.value
            
        docs = await self.find(query, limit=1)
        return docs[0] if docs else None
        
    async def get_all_active(self) -> List[OutputContract]:
        return await self.find({"status": OutputContractStatus.ACTIVE.value}, limit=100)
