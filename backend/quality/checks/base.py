from typing import Dict, Any, Optional
from pydantic import BaseModel
from abc import ABC, abstractmethod

from ..models import QualityCheck, QualityCheckType
from ..results import QualityCheckResult

class QualityEvaluationContext(BaseModel):
    """
    Provides the isolated context required for a check to evaluate.
    """
    execution_id: str
    stage_execution_id: Optional[str] = None
    pipeline_execution_id: Optional[str] = None
    
    # Information available to check
    artifacts: Dict[str, Any] = {} # e.g., artifact_id -> ArtifactReference
    outputs: Dict[str, Any] = {}
    inputs: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}

class BaseQualityCheckExecutor(ABC):
    
    @property
    @abstractmethod
    def check_type(self) -> QualityCheckType:
        pass
        
    @abstractmethod
    async def execute(self, check: QualityCheck, context: QualityEvaluationContext) -> QualityCheckResult:
        """Executes the check and returns the result."""
        pass
