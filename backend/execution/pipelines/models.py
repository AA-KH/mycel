from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from enum import Enum

class PipelineStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"

class StageType(str, Enum):
    INPUT = "input"
    ANALYSIS = "analysis"
    RESEARCH = "research"
    RETRIEVAL = "retrieval"
    PLANNING = "planning"
    EXECUTION = "execution"
    VERIFICATION = "verification"
    REVIEW = "review"
    TRANSFORMATION = "transformation"
    GENERATION = "generation"
    OUTPUT = "output"

class ExecutionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"
    BLOCKED = "blocked"

# ---------------------------------------------------------
# Pipeline Topology
# ---------------------------------------------------------
class PipelineStage(BaseModel):
    """
    Defines a single node in the workflow graph.
    """
    stage_id: str
    name: str
    display_name: str
    description: str = ""
    order: int
    
    stage_definition_id: str
    stage_definition_version: str = "1.0.0"
    
    pre_gate_id: Optional[str] = None
    post_gate_id: Optional[str] = None
    
    status: str = "active"
    required: bool = True
    
    depends_on: List[str] = Field(default_factory=list) # List of stage_ids that must complete first
    
    max_attempts: int = 1
    retryable: bool = False
    
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PipelineInputContract(BaseModel):
    input_type: str
    required: bool = True
    description: str = ""

class TeamPipeline(BaseModel):
    """
    The aggregate root for a structured team pipeline.
    """
    id: Optional[str] = None
    pipeline_id: str
    team_id: str
    name: str
    display_name: str
    description: str = ""
    version: str = "1.0.0"
    status: PipelineStatus = PipelineStatus.DRAFT
    
    input_contract: PipelineInputContract
    output_contract_id: Optional[str] = None
    stages: List[PipelineStage] = Field(default_factory=list)
    
    pipeline_gate_ids: List[str] = Field(default_factory=list)
    
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# ---------------------------------------------------------
# Execution State
# ---------------------------------------------------------
class StageExecutionState(BaseModel):
    stage_id: str
    status: ExecutionStatus = ExecutionStatus.PENDING
    attempt: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    output_reference: Optional[str] = None # e.g. ArtifactReference
    metadata: Dict[str, Any] = Field(default_factory=dict)

class PipelineExecution(BaseModel):
    """
    Tracks the execution of a pipeline.
    """
    id: Optional[str] = None
    execution_id: str
    pipeline_id: str
    pipeline_version: str
    team_id: str
    task_id: str
    status: ExecutionStatus = ExecutionStatus.PENDING
    
    current_stage_id: Optional[str] = None
    stage_states: Dict[str, StageExecutionState] = Field(default_factory=dict) # Keyed by stage_id
    
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
