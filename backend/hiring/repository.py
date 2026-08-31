from abc import ABC, abstractmethod
from typing import List, Optional
from .models import HiringDecision

class HiringDecisionRepository(ABC):
    @abstractmethod
    async def save(self, decision: HiringDecision) -> HiringDecision:
        pass

    @abstractmethod
    async def get_by_task(self, task_id: str) -> List[HiringDecision]:
        pass

class InMemoryHiringDecisionRepository(HiringDecisionRepository):
    def __init__(self):
        self._store = {}
        
    async def save(self, decision: HiringDecision) -> HiringDecision:
        self._store[decision.decision_id] = decision
        return decision
        
    async def get_by_task(self, task_id: str) -> List[HiringDecision]:
        return [d for d in self._store.values() if d.task_id == task_id]

# Note: MongoHiringDecisionRepository to be implemented later when integrated with full MongoDB driver
class MongoHiringDecisionRepository(HiringDecisionRepository):
    def __init__(self, db):
        self.collection = db.hiring_decisions
        
    async def save(self, decision: HiringDecision) -> HiringDecision:
        # Pydantic v2 compatible dict dump
        data = decision.model_dump()
        await self.collection.insert_one(data)
        return decision
        
    async def get_by_task(self, task_id: str) -> List[HiringDecision]:
        docs = await self.collection.find({"task_id": task_id}).to_list(length=None)
        return [HiringDecision(**doc) for doc in docs]
