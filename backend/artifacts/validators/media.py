import mimetypes
import os
from typing import Dict, Any

from .base import BaseValidator
from ..models import ArtifactValidationResult

class VideoValidator(BaseValidator):
    """
    Validates video artifacts produced by creative media tools.

    Checks:
        1. File exists
        2. MIME type starts with 'video/'
        3. File size > 0 bytes (non-empty; catches silent generation failures)

    ComfyUI returning HTTP 200 is NOT sufficient — we verify the output is a valid,
    non-empty video file before creating an ArtifactReference.
    """

    def validate(self, artifact_id: str, file_path: str, expected_output: Dict[str, Any]) -> ArtifactValidationResult:
        checks = []
        status = "passed"
        reason = None

        # 1. File existence
        if not os.path.exists(file_path):
            return ArtifactValidationResult(
                artifact_id=artifact_id,
                status="failed",
                reason="Video file does not exist.",
            )
        checks.append({"name": "file_exists", "status": "passed"})

        # 2. Non-zero size (catches silent generation failures)
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            return ArtifactValidationResult(
                artifact_id=artifact_id,
                status="failed",
                checks=[{"name": "file_exists", "status": "passed"},
                        {"name": "non_zero_size", "status": "failed"}],
                reason="Video file is empty (0 bytes). Generation may have failed silently.",
            )
        checks.append({"name": "non_zero_size", "status": "passed"})

        # 3. MIME type
        expected_mime = expected_output.get("mime_type", "video/mp4")
        actual_mime, _ = mimetypes.guess_type(file_path)

        if not actual_mime or not actual_mime.startswith("video/"):
            checks.append({
                "name": "mime_type",
                "status": "failed",
                "details": f"Expected video/*, got {actual_mime}",
            })
            status = "failed"
            reason = f"File is not a valid video type (detected: {actual_mime})."
        else:
            checks.append({"name": "mime_type", "status": "passed"})

        return ArtifactValidationResult(
            artifact_id=artifact_id,
            status=status,
            checks=checks,
            reason=reason,
        )


class ImageValidator(BaseValidator):
    def validate(self, artifact_id: str, file_path: str, expected_output: Dict[str, Any]) -> ArtifactValidationResult:
        if not os.path.exists(file_path):
            return ArtifactValidationResult(artifact_id=artifact_id, status="failed", reason="File does not exist.")
            
        expected_mime = expected_output.get("mime_type", "image/png")
        actual_mime, _ = mimetypes.guess_type(file_path)
        
        if not actual_mime or not actual_mime.startswith("image/"):
            return ArtifactValidationResult(
                artifact_id=artifact_id, 
                status="failed", 
                checks=[{"name": "mime_type", "status": "failed"}], 
                reason="Not a valid image type"
            )
            
        return ArtifactValidationResult(
            artifact_id=artifact_id, status="passed", checks=[{"name": "mime_type", "status": "passed"}]
        )
