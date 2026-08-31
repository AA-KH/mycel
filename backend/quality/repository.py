from typing import List, Optional
from infrastructure.database.repositories.base import BaseRepository
from .models import QualityGate, QualityGateStatus, QualityGateScope
from .results import QualityGateResult

class QualityGateRepository(BaseRepository[QualityGate]):
    def __init__(self, db):
        super().__init__(db, "quality_gates", QualityGate)

    async def get_by_gate_id(self, quality_gate_id: str, version: Optional[str] = None) -> Optional[QualityGate]:
        query = {"quality_gate_id": quality_gate_id}
        if version:
            query["version"] = version
        else:
            query["status"] = QualityGateStatus.ACTIVE.value
            
        docs = await self.find(query, limit=1)
        return docs[0] if docs else None
        
    async def get_all_active(self) -> List[QualityGate]:
        return await self.find({"status": QualityGateStatus.ACTIVE.value}, limit=100)

class QualityExecutionRepository(BaseRepository[QualityGateResult]):
    def __init__(self, db):
        super().__init__(db, "quality_gate_executions", QualityGateResult)
