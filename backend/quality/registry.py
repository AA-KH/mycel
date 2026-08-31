from typing import List, Optional
from core.errors import DomainError

from .repository import QualityGateRepository
from .models import QualityGate
from .validator import QualityGateValidator

class QualityGateRegistry:
    def __init__(self, repository: QualityGateRepository):
        self.repository = repository

    async def get_gate(self, quality_gate_id: str, version: Optional[str] = None) -> Optional[QualityGate]:
        return await self.repository.get_by_gate_id(quality_gate_id, version)

    async def get_all_active(self) -> List[QualityGate]:
        return await self.repository.get_all_active()

    async def register_gate(self, gate: QualityGate) -> QualityGate:
        # Prevent registering duplicate ID+Version combinations
        existing = await self.get_gate(gate.quality_gate_id, gate.version)
        if existing:
            raise DomainError(f"QualityGate '{gate.quality_gate_id}' version '{gate.version}' already exists.")
            
        QualityGateValidator.validate_gate(gate)
        return await self.repository.create(gate)
