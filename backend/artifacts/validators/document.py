import mimetypes
import os
from typing import Dict, Any

from .base import BaseValidator
from ..models import ArtifactValidationResult

class DocumentValidator(BaseValidator):
    def validate(self, artifact_id: str, file_path: str, expected_output: Dict[str, Any]) -> ArtifactValidationResult:
        if not os.path.exists(file_path):
            return ArtifactValidationResult(artifact_id=artifact_id, status="failed", reason="File does not exist.")
            
        # Basic validation: ensure it's not a 0 byte file
        size = os.path.getsize(file_path)
        if size == 0:
            return ArtifactValidationResult(artifact_id=artifact_id, status="failed", reason="Document is empty (0 bytes).")
            
        return ArtifactValidationResult(
            artifact_id=artifact_id, status="passed", checks=[{"name": "size", "status": "passed"}]
        )
