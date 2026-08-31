from typing import Dict, Any, Optional
from pydantic import BaseModel
from .models import PipelineExecution, StageExecutionState, ExecutionStatus, TeamPipeline
from .repository import PipelineExecutionRepository

class StageContext(BaseModel):
    task_id: str
    team_id: str
    pipeline_id: str
    stage_id: str
    previous_outputs: Dict[str, str] = {} # Keyed by previous stage_id, value is ArtifactReference
    
class PipelineResult(BaseModel):
    success: bool
    pipeline_id: str
    execution_id: str
    outputs: Dict[str, str] = {} # Keyed by stage_id
    errors: Dict[str, str] = {}
    metadata: Dict[str, Any] = {}

class PipelineExecutor:
    """
    Contract for pipeline execution. Establishes state transitions but stops short 
    of implementing the full multi-agent orchestrator.
    """
    def __init__(self, execution_repo: PipelineExecutionRepository):
        self.execution_repo = execution_repo
        
    async def initialize_execution(self, pipeline: TeamPipeline, task_id: str) -> PipelineExecution:
        import uuid
        from datetime import datetime, timezone
        
        execution_id = f"exec_{uuid.uuid4().hex[:8]}"
        stage_states = {}
        
        for stage in pipeline.stages:
            stage_states[stage.stage_id] = StageExecutionState(
                stage_id=stage.stage_id,
                status=ExecutionStatus.PENDING
            )
            
        execution = PipelineExecution(
            execution_id=execution_id,
            pipeline_id=pipeline.pipeline_id,
            pipeline_version=pipeline.version,
            team_id=pipeline.team_id,
            task_id=task_id,
            status=ExecutionStatus.PENDING,
            stage_states=stage_states,
            started_at=datetime.now(timezone.utc)
        )
        return await self.execution_repo.create(execution)
        
    async def update_stage_status(self, execution_id: str, stage_id: str, status: ExecutionStatus, output_ref: Optional[str] = None):
        execution = await self.execution_repo.get_by_execution_id(execution_id)
        if not execution:
            raise ValueError("Execution not found")
            
        if stage_id not in execution.stage_states:
            raise ValueError(f"Stage {stage_id} not found in execution {execution_id}")
            
        from datetime import datetime, timezone
        state = execution.stage_states[stage_id]
        state.status = status
        
        if status == ExecutionStatus.COMPLETED:
            state.completed_at = datetime.now(timezone.utc)
            if output_ref:
                state.output_reference = output_ref
                
        await self.execution_repo.update(execution.id, execution.model_dump())
