from abc import ABC, abstractmethod
from typing import Dict, Any

from ..models import ArtifactValidationResult

class BaseValidator(ABC):
    """
    Abstract base class for all Artifact validators.
    """
    
    @abstractmethod
    def validate(self, artifact_id: str, file_path: str, expected_output: Dict[str, Any]) -> ArtifactValidationResult:
        """
        Validates the file against the expected output contract.
        """
        pass
