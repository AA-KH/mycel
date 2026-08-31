from .models import Artifact, ArtifactReference, ArtifactStatus, ArtifactValidationResult
from .repository import ArtifactRepository, InMemoryArtifactRepository, MongoArtifactRepository
from .service import ArtifactService, ArtifactValidationException
from .delivery import ArtifactDeliveryService
from .storage import get_storage_provider, StorageProvider, MockStorageProvider, CloudinaryStorageProvider

__all__ = [
    "ArtifactReference",
    "ArtifactStatus",
    "ArtifactValidationResult",
    "ArtifactRepository",
    "InMemoryArtifactRepository",
    "MongoArtifactRepository",
    "ArtifactService",
    "ArtifactValidationException",
    "ArtifactDeliveryService",
    "get_storage_provider",
    "StorageProvider",
    "MockStorageProvider",
    "CloudinaryStorageProvider",
    "get_artifact_service"
]

_artifact_service = None

def get_artifact_service() -> ArtifactService:
    global _artifact_service
    if _artifact_service is None:
        # We default to InMemory for test/mock compatibility. 
        # In a real deployed environment, main.py injects MongoArtifactRepository.
        repo = InMemoryArtifactRepository()
        storage = get_storage_provider()
        _artifact_service = ArtifactService(repo, storage)
    return _artifact_service

