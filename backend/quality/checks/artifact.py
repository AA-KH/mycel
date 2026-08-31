from typing import Any, Dict
import logging
from ..models import QualityCheck, QualityCheckType
from ..results import QualityCheckResult, QualityCheckResultStatus
from .base import BaseQualityCheckExecutor, QualityEvaluationContext

# We assume ArtifactService or Validators would be injected/imported here.
# For TOS 8, we simulate the delegation to the Artifact Validator system.

logger = logging.getLogger(__name__)

class ArtifactExistsCheckExecutor(BaseQualityCheckExecutor):
    """
    Checks if a required artifact was correctly registered in the context.
    """
    @property
    def check_type(self) -> QualityCheckType:
        return QualityCheckType.EXISTS

    async def execute(self, check: QualityCheck, context: QualityEvaluationContext) -> QualityCheckResult:
        # Configuration should specify which artifact key to look for
        artifact_key = check.configuration.get("artifact_key")
        if not artifact_key:
            return QualityCheckResult(
                check_id=check.check_id,
                status=QualityCheckResultStatus.ERROR,
                message="Configuration missing 'artifact_key'."
            )
            
        artifact_ref = context.artifacts.get(artifact_key)
        
        if artifact_ref:
            return QualityCheckResult(
                check_id=check.check_id,
                status=QualityCheckResultStatus.PASS,
                message=f"Artifact '{artifact_key}' exists.",
                evidence={"artifact_id": getattr(artifact_ref, "artifact_id", str(artifact_ref))}
            )
        else:
            return QualityCheckResult(
                check_id=check.check_id,
                status=QualityCheckResultStatus.FAIL,
                message=f"Artifact '{artifact_key}' does not exist in context."
            )

class ArtifactFormatCheckExecutor(BaseQualityCheckExecutor):
    """
    Checks if an artifact is of the correct format (e.g., .mp4, .pdf).
    In a full implementation, this delegates to ArtifactService validators.
    """
    @property
    def check_type(self) -> QualityCheckType:
        return QualityCheckType.FORMAT

    async def execute(self, check: QualityCheck, context: QualityEvaluationContext) -> QualityCheckResult:
        artifact_key = check.configuration.get("artifact_key")
        expected_format = check.configuration.get("expected_format")
        
        if not artifact_key or not expected_format:
            return QualityCheckResult(
                check_id=check.check_id,
                status=QualityCheckResultStatus.ERROR,
                message="Configuration missing 'artifact_key' or 'expected_format'."
            )
            
        artifact_ref = context.artifacts.get(artifact_key)
        if not artifact_ref:
            # We fail on non-existence if this check is required
            return QualityCheckResult(
                check_id=check.check_id,
                status=QualityCheckResultStatus.FAIL,
                message=f"Artifact '{artifact_key}' does not exist, cannot check format."
            )
            
        # Simulate format validation check against the ArtifactSystem.
        # In reality, this would be: `await artifact_service.validate(...)`
        actual_format = getattr(artifact_ref, "format", None)
        
        if actual_format == expected_format:
            return QualityCheckResult(
                check_id=check.check_id,
                status=QualityCheckResultStatus.PASS,
                message=f"Artifact format '{actual_format}' matches expected '{expected_format}'.",
                evidence={"artifact_id": getattr(artifact_ref, "artifact_id", "unknown"), "format": actual_format}
            )
        else:
            return QualityCheckResult(
                check_id=check.check_id,
                status=QualityCheckResultStatus.FAIL,
                message=f"Artifact format '{actual_format}' does NOT match expected '{expected_format}'.",
                evidence={"artifact_id": getattr(artifact_ref, "artifact_id", "unknown"), "format": actual_format}
            )
