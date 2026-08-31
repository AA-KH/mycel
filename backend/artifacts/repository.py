from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import motor.motor_asyncio
from bson import ObjectId

from .models import Artifact, ArtifactStatus

class ArtifactRepository(ABC):
    """
    Abstract interface for Artifact Persistence.
    """
    @abstractmethod
    async def create(self, artifact: Artifact) -> Artifact:
        pass

    @abstractmethod
    async def get(self, artifact_id: str) -> Optional[Artifact]:
        pass

    @abstractmethod
    async def update(self, artifact_id: str, updates: Dict[str, Any]) -> Optional[Artifact]:
        pass

    @abstractmethod
    async def update_status(self, artifact_id: str, status: ArtifactStatus) -> Optional[Artifact]:
        pass

    @abstractmethod
    async def delete(self, artifact_id: str) -> bool:
        pass

    @abstractmethod
    async def find_by_task(self, task_id: str) -> List[Artifact]:
        pass

    @abstractmethod
    async def find_by_execution(self, execution_id: str) -> List[Artifact]:
        pass


class InMemoryArtifactRepository(ArtifactRepository):
    """
    In-memory Mock Repository for Artifacts used in unit tests.
    """
    def __init__(self):
        self._artifacts: Dict[str, Artifact] = {}

    async def create(self, artifact: Artifact) -> Artifact:
        self._artifacts[artifact.artifact_id] = artifact
        return artifact

    async def get(self, artifact_id: str) -> Optional[Artifact]:
        return self._artifacts.get(artifact_id)

    async def update(self, artifact_id: str, updates: Dict[str, Any]) -> Optional[Artifact]:
        artifact = await self.get(artifact_id)
        if not artifact:
            return None
            
        for key, value in updates.items():
            if hasattr(artifact, key):
                setattr(artifact, key, value)
        
        artifact.updated_at = datetime.now(timezone.utc)
        self._artifacts[artifact_id] = artifact
        return artifact

    async def update_status(self, artifact_id: str, status: ArtifactStatus) -> Optional[Artifact]:
        return await self.update(artifact_id, {"status": status})

    async def delete(self, artifact_id: str) -> bool:
        if artifact_id in self._artifacts:
            del self._artifacts[artifact_id]
            return True
        return False

    async def find_by_task(self, task_id: str) -> List[Artifact]:
        return [a for a in self._artifacts.values() if a.task_id == task_id]

    async def find_by_execution(self, execution_id: str) -> List[Artifact]:
        return [a for a in self._artifacts.values() if a.execution_id == execution_id]


class MongoArtifactRepository(ArtifactRepository):
    """
    Production repository storing artifacts in MongoDB.
    """
    def __init__(self, db: motor.motor_asyncio.AsyncIOMotorDatabase):
        self.collection = db["artifacts"]
        
    async def _setup_indexes(self):
        await self.collection.create_index("artifact_id", unique=True)
        await self.collection.create_index("company_id")
        await self.collection.create_index("task_id")
        await self.collection.create_index("execution_id")
        await self.collection.create_index("employee_id")

    async def create(self, artifact: Artifact) -> Artifact:
        doc = artifact.model_dump()
        doc["status"] = artifact.status.value # Convert enum to string for mongo
        await self.collection.insert_one(doc)
        return artifact

    async def get(self, artifact_id: str) -> Optional[Artifact]:
        doc = await self.collection.find_one({"artifact_id": artifact_id})
        if not doc:
            return None
        doc.pop("_id", None)
        return Artifact(**doc)

    async def update(self, artifact_id: str, updates: Dict[str, Any]) -> Optional[Artifact]:
        updates["updated_at"] = datetime.now(timezone.utc)
        # Ensure enums are converted if updated directly
        if "status" in updates and isinstance(updates["status"], ArtifactStatus):
            updates["status"] = updates["status"].value
            
        result = await self.collection.find_one_and_update(
            {"artifact_id": artifact_id},
            {"$set": updates},
            return_document=motor.motor_asyncio.ReturnDocument.AFTER
        )
        if not result:
            return None
        result.pop("_id", None)
        return Artifact(**result)

    async def update_status(self, artifact_id: str, status: ArtifactStatus) -> Optional[Artifact]:
        return await self.update(artifact_id, {"status": status})

    async def delete(self, artifact_id: str) -> bool:
        result = await self.collection.delete_one({"artifact_id": artifact_id})
        return result.deleted_count > 0

    async def find_by_task(self, task_id: str) -> List[Artifact]:
        cursor = self.collection.find({"task_id": task_id})
        results = await cursor.to_list(length=None)
        artifacts = []
        for doc in results:
            doc.pop("_id", None)
            artifacts.append(Artifact(**doc))
        return artifacts

    async def find_by_execution(self, execution_id: str) -> List[Artifact]:
        cursor = self.collection.find({"execution_id": execution_id})
        results = await cursor.to_list(length=None)
        artifacts = []
        for doc in results:
            doc.pop("_id", None)
            artifacts.append(Artifact(**doc))
        return artifacts
