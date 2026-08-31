from typing import List, Optional
from core.errors import DomainError

from .repository import StageDefinitionRepository
from .models import StageDefinition, StageDefinitionStatus
from .validator import StageDefinitionValidator

class StageDefinitionRegistry:
    def __init__(self, repository: StageDefinitionRepository):
        self.repository = repository

    async def get_definition(self, stage_definition_id: str, version: Optional[str] = None) -> Optional[StageDefinition]:
        return await self.repository.get_by_definition_id(stage_definition_id, version)

    async def get_all_active(self) -> List[StageDefinition]:
        return await self.repository.get_all_active()

    async def register_definition(self, definition: StageDefinition) -> StageDefinition:
        # Prevent registering duplicate ID+Version combinations
        existing = await self.get_definition(definition.stage_definition_id, definition.version)
        if existing:
            raise DomainError(f"StageDefinition '{definition.stage_definition_id}' version '{definition.version}' already exists.")
            
        # Basic structural validation
        StageDefinitionValidator.validate_definition(definition)
        
        return await self.repository.create(definition)
