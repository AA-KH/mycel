"""
Evaluation System Models (Phase 13)

Defines the structure of Evaluations, Dimensions, Evidence, and Insights.
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class EvaluationStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class EvaluationType(str, Enum):
    TASK = "TASK"
    WORK_UNIT = "WORK_UNIT"
    OUTPUT = "OUTPUT"
    TEAM = "TEAM"
    COLLABORATION = "COLLABORATION"
    PIPELINE = "PIPELINE"
    AGENT = "AGENT"
    EXECUTION = "EXECUTION"


class EvaluationMethod(str, Enum):
    DETERMINISTIC = "DETERMINISTIC"
    RULE_BASED = "RULE_BASED"
    CONTRACT_BASED = "CONTRACT_BASED"
    QUALITY_BASED = "QUALITY_BASED"
    METRIC_BASED = "METRIC_BASED"
    LLM_ASSISTED = "LLM_ASSISTED"


class EvaluationEvidenceSource(str, Enum):
    TASK = "TASK"
    WORK_UNIT = "WORK_UNIT"
    ARTIFACT = "ARTIFACT"
    QUALITY_GATE = "QUALITY_GATE"
    TOOL = "TOOL"
    COLLABORATION = "COLLABORATION"
    MEMORY = "MEMORY"
    METRIC = "METRIC"
    USER_FEEDBACK = "USER_FEEDBACK"


class EvaluationFailureCategory(str, Enum):
    REQUIREMENT_FAILURE = "REQUIREMENT_FAILURE"
    CONTRACT_FAILURE = "CONTRACT_FAILURE"
    QUALITY_FAILURE = "QUALITY_FAILURE"
    TOOL_FAILURE = "TOOL_FAILURE"
    COLLABORATION_FAILURE = "COLLABORATION_FAILURE"
    RUNTIME_FAILURE = "RUNTIME_FAILURE"
    TIMEOUT = "TIMEOUT"
    RESOURCE_FAILURE = "RESOURCE_FAILURE"
    USER_REJECTION = "USER_REJECTION"
    EVALUATION_FAILURE = "EVALUATION_FAILURE"


class EvaluationEvidence(BaseModel):
    evidence_id: str
    evaluation_id: Optional[str] = None
    type: str
    source: EvaluationEvidenceSource
    source_reference: str
    summary: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EvaluationFailure(BaseModel):
    category: EvaluationFailureCategory
    root_cause: str
    evidence: List[EvaluationEvidence] = Field(default_factory=list)
    confidence: float = 1.0


class EvaluationDimension(BaseModel):
    name: str
    score: Optional[float] = None
    max_score: float = 1.0
    weight: float = 1.0
    method: EvaluationMethod
    evidence: List[EvaluationEvidence] = Field(default_factory=list)
    confidence: float = 1.0
    evaluated: bool = False
    
    @property
    def is_missing(self) -> bool:
        return not self.evaluated


class EvaluationInsight(BaseModel):
    insight_id: str
    summary: str
    confidence: float = 1.0
    evidence: List[EvaluationEvidence] = Field(default_factory=list)


class EvaluationFeedback(BaseModel):
    feedback_id: str
    task_id: Optional[str] = None
    artifact_id: Optional[str] = None
    rating: int  # e.g., 1 to 5
    comment: str = ""
    accepted: bool = True
    type: str = "USER"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source: str = "USER_INTERFACE"


class Evaluation(BaseModel):
    evaluation_id: str
    task_id: Optional[str] = None
    work_unit_id: Optional[str] = None
    team_id: Optional[str] = None
    employee_id: Optional[str] = None
    agent_id: Optional[str] = None
    pipeline_id: Optional[str] = None
    
    evaluation_type: EvaluationType
    status: EvaluationStatus = EvaluationStatus.PENDING
    
    score: Optional[float] = None  # Overall weighted score
    dimensions: List[EvaluationDimension] = Field(default_factory=list)
    
    evidence: List[EvaluationEvidence] = Field(default_factory=list)
    failures: List[EvaluationFailure] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    insights: List[EvaluationInsight] = Field(default_factory=list)
    
    policy_version: str = "1.0.0"
    version: int = 1
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)
