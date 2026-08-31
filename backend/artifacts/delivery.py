from typing import Dict, Any, Optional

from .models import Artifact

class ArtifactDeliveryService:
    """
    Responsible for transforming a backend Artifact record into a safe, UI-facing representation.
    Prevents leaking internal storage keys, credentials, or backend-only metadata.
    """
    
    @staticmethod
    def deliver(artifact: Artifact) -> Optional[Dict[str, Any]]:
        if not artifact or artifact.status != "ready":
            return None
            
        return {
            "artifact_id": artifact.artifact_id,
            "type": artifact.type,
            "filename": artifact.filename,
            "mime_type": artifact.mime_type,
            "size_bytes": artifact.size_bytes,
            "url": artifact.secure_url or artifact.url,
            "status": artifact.status.value,
            "created_at": artifact.created_at.isoformat()
        }
