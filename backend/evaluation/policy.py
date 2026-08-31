"""
Evaluation Policy (Phase 13)

Defines how a specific target is evaluated, which dimensions apply, 
their weights, and if semantic evaluation is allowed.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from evaluation.models import EvaluationType, EvaluationMethod


class DimensionConfiguration(BaseModel):
    name: str
    weight: float = 1.0
    required: bool = True
    method: EvaluationMethod = EvaluationMethod.DETERMINISTIC
    max_score: float = 1.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EvaluationPolicy(BaseModel):
    policy_id: str
    version: str = "1.0.0"
    target_type: EvaluationType
    
    dimensions: List[DimensionConfiguration] = Field(default_factory=list)
    
    # Thresholds mapping, e.g., {"score": 0.8} for passing
    thresholds: Dict[str, float] = Field(default_factory=dict)
    
    # Whether semantic evaluation is allowed for this policy
    allows_semantic: bool = False
    
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def get_dimension_config(self, name: str) -> Optional[DimensionConfiguration]:
        for dim in self.dimensions:
            if dim.name == name:
                return dim
        return None
