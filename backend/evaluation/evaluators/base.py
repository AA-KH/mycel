"""
Base Evaluator Interface (Phase 13)

Defines the Evaluator interface and context for evaluation.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from evaluation.models import EvaluationDimension, EvaluationMethod
from evaluation.policy import DimensionConfiguration
from artifacts.models import ArtifactReference
from tasks.models import Task, WorkUnit
from quality.results import QualityGateResult


class EvaluationContext(BaseModel):
    """
    Minimal context required for evaluation. Follows MINIMUM REQUIRED DATA principle.
    """
    task: Optional[Task] = None
    work_unit: Optional[WorkUnit] = None
    
    # Input/Output artifacts related to the evaluation target
    artifacts: List[ArtifactReference] = Field(default_factory=list)
    
    # Existing Quality Gate Results
    quality_results: List[QualityGateResult] = Field(default_factory=list)
    
    # Execution metrics (e.g., latency, token count, retry count)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Evaluator(ABC):
    """
    Base interface for all Evaluators. 
    Each Evaluator should be small, deterministic where possible, and replaceable.
    """
    
    @property
    @abstractmethod
    def method(self) -> EvaluationMethod:
        """The primary method this evaluator uses."""
        pass
        
    @abstractmethod
    async def evaluate(self, config: DimensionConfiguration, context: EvaluationContext) -> EvaluationDimension:
        """
        Executes the evaluation logic for a specific dimension configuration.
        """
        pass
