from typing import Dict, Any, Optional, List
import mimetypes
import os
import hashlib
from datetime import datetime, timezone

from .models import Artifact, ArtifactStatus, ArtifactReference, ArtifactValidationResult
from .repository import ArtifactRepository
from .validators import get_validator_for_type
from .storage import get_storage_provider, StorageProvider
from core.logger import logger

class ArtifactValidationException(Exception):
    def __init__(self, validation_result: ArtifactValidationResult):
        super().__init__(f"Artifact validation failed: {validation_result.reason}")
        self.validation_result = validation_result

class ArtifactService:
    """
    Core service orchestrating Artifact creation, validation, and storage.
    """
    def __init__(self, repository: ArtifactRepository, storage_provider: StorageProvider):
        self.repository = repository
        self.storage = storage_provider

    async def _calculate_checksum(self, file_path: str) -> str:
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    async def create_and_store(
        self,
        company_id: str,
        workspace_id: str,
        task_id: str,
        execution_id: str,
        employee_id: str,
        artifact_type: str,
        file_path: str,
        expected_output: Dict[str, Any],
        parent_artifact_id: Optional[str] = None
    ) -> ArtifactReference:
        """
        Full lifecycle: Create DB record -> Validate -> Upload -> Mark Ready.
        """
        filename = os.path.basename(file_path)
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            mime_type = "application/octet-stream"
            
        size_bytes = os.path.getsize(file_path) if os.path.exists(file_path) else 0

        # Create record
        artifact = Artifact(
            company_id=company_id,
            workspace_id=workspace_id,
            task_id=task_id,
            execution_id=execution_id,
            employee_id=employee_id,
            type=artifact_type,
            mime_type=mime_type,
            filename=filename,
            size_bytes=size_bytes,
            status=ArtifactStatus.CREATED,
            storage_provider=self.storage.__class__.__name__,
            storage_key="", # Will update after upload
            parent_artifact_id=parent_artifact_id
        )
        
        await self.repository.create(artifact)
        
        try:
            # 1. Validation
            await self.repository.update_status(artifact.artifact_id, ArtifactStatus.VALIDATING)
            
            validator = get_validator_for_type(artifact_type)
            val_result = validator.validate(artifact.artifact_id, file_path, expected_output)
            
            if val_result.status != "passed":
                await self.repository.update_status(artifact.artifact_id, ArtifactStatus.FAILED)
                raise ArtifactValidationException(val_result)
                
            # 2. Hash
            checksum = await self._calculate_checksum(file_path)
            await self.repository.update(artifact.artifact_id, {"checksum": checksum})
            
            # 3. Upload
            await self.repository.update_status(artifact.artifact_id, ArtifactStatus.UPLOADING)
            
            # Construct a safe tenant-aware path
            destination_path = f"mycel/companies/{company_id}/tasks/{task_id}/{artifact.artifact_id}_{filename}"
            
            upload_result = await self.storage.upload(file_path, destination_path, resource_type=artifact_type)
            
            # 4. Finalize
            await self.repository.update(artifact.artifact_id, {
                "status": ArtifactStatus.READY,
                "storage_key": upload_result.get("storage_key", destination_path),
                "url": upload_result.get("url"),
                "secure_url": upload_result.get("secure_url"),
                "size_bytes": upload_result.get("size_bytes", size_bytes)
            })
            
            # In a real system, we'd emit an event here: `artifact.ready`
            
            # Return Reference
            return ArtifactReference(
                artifact_id=artifact.artifact_id,
                type=artifact_type,
                mime_type=mime_type,
                size_bytes=upload_result.get("size_bytes", size_bytes),
                storage=self.storage.__class__.__name__,
                url=upload_result.get("secure_url") or upload_result.get("url")
            )
            
        except ArtifactValidationException:
            raise
        except Exception as e:
            logger.error(f"Upload failed for artifact {artifact.artifact_id}: {e}")
            await self.repository.update_status(artifact.artifact_id, ArtifactStatus.FAILED)
            raise RuntimeError(f"Artifact creation failed: {e}")

    async def get_artifact(self, artifact_id: str) -> Optional[Artifact]:
        return await self.repository.get(artifact_id)

    async def delete_artifact(self, artifact_id: str) -> bool:
        artifact = await self.repository.get(artifact_id)
        if not artifact:
            return False
            
        await self.repository.update_status(artifact_id, ArtifactStatus.DELETED)
        
        # Delete from storage provider
        deleted = await self.storage.delete(artifact.storage_key, resource_type=artifact.type)
        if not deleted:
            logger.warning(f"Failed to delete artifact {artifact_id} from storage provider.")
            
        return True
