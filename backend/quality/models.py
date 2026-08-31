from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from enum import Enum

class QualityGateScope(str, Enum):
    STAGE = "stage"
    PIPELINE = "pipeline"
    OUTPUT = "output"
    ARTIFACT = "artifact"
    TASK = "task"

class QualityGateStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"

class QualityGateDecision(str, Enum):
    PASS = "pass"
    RETRY = "retry"
    BLOCK = "block"
    FAIL = "fail"
    ESCALATE = "escalate"

class QualityCheckSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class QualityPolicy(str, Enum):
    ALL_REQUIRED_PASS = "all_required_pass"
    MINIMUM_SCORE = "minimum_score"
    CRITICAL_FAILURE_BLOCKS = "critical_failure_blocks"
    MAJORITY_PASS = "majority_pass"

class QualityCheckType(str, Enum):
    EXISTS = "exists"
    SCHEMA = "schema"
    FORMAT = "format"
    SIZE = "size"
    METADATA = "metadata"
    CONTENT = "content"
    REFERENCE = "reference"
    CITATION = "citation"
    SOURCE_TRUST = "source_trust"
    COMPLETENESS = "completeness"
    CONSISTENCY = "consistency"
    TEST = "test"
    POLICY = "policy"
    LLM_REVIEW = "llm_review"
    HUMAN_REVIEW = "human_review"

# ---------------------------------------------------------
# Check Definition
# ---------------------------------------------------------
class QualityCheck(BaseModel):
    check_id: str
    name: str
    type: QualityCheckType
    description: str = ""
    required: bool = True
    severity: QualityCheckSeverity = QualityCheckSeverity.ERROR
    configuration: Dict[str, Any] = Field(default_factory=dict)
    order: int = 1
    metadata: Dict[str, Any] = Field(default_factory=dict)

# ---------------------------------------------------------
# Gate Definition (Aggregate Root)
# ---------------------------------------------------------
class QualityGate(BaseModel):
    id: Optional[str] = None
    quality_gate_id: str
    name: str
    display_name: str
    description: str = ""
    scope: QualityGateScope = QualityGateScope.STAGE
    version: str = "1.0.0"
    status: QualityGateStatus = QualityGateStatus.DRAFT
    severity: QualityCheckSeverity = QualityCheckSeverity.ERROR
    
    checks: List[QualityCheck] = Field(default_factory=list)
    policy: QualityPolicy = QualityPolicy.ALL_REQUIRED_PASS
    minimum_score: Optional[int] = None
    
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
