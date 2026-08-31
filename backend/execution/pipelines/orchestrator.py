"""
Pipeline Orchestrator

Responsible for executing a TeamPipeline sequentially by dispatching each stage
as a contextualized task to the AgentRuntime.
"""

from typing import Dict, Any, List
import json
import logging

from .models import TeamPipeline
from agents.runtime.lifecycle import AgentRuntime
from agents.runtime.context import ExecutionContext
from agents.runtime.snapshot import ExecutionSnapshot

logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    """
    Executes a TeamPipeline stage by stage.
    """
    
    def __init__(self, runtime: AgentRuntime):
        self.runtime = runtime

    async def execute_pipeline(
        self, 
        pipeline: TeamPipeline, 
        initial_task: Dict[str, Any], 
        snapshot: ExecutionSnapshot,
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """
        Execute the pipeline stages in order.
        Passes the output of previous stages into the context of the next stage.
        """
        logger.info(f"Starting execution of pipeline: {pipeline.pipeline_id}")
        
        # Sort stages by order
        stages = sorted(pipeline.stages, key=lambda s: s.order)
        
        stage_outputs = {}
        
        for stage in stages:
            logger.info(f"Executing pipeline stage: {stage.stage_id} ({stage.display_name})")
            
            # Build the prompt for this specific stage
            stage_prompt = (
                f"You are executing stage: {stage.display_name} ({stage.stage_id}).\n"
                f"Description: {stage.description}\n\n"
            )
            
            if stage_outputs:
                stage_prompt += "Here are the outputs from previous stages:\n"
                for s_id, out in stage_outputs.items():
                    stage_prompt += f"--- Output from {s_id} ---\n"
                    stage_prompt += f"{json.dumps(out, indent=2)}\n\n"
            
            stage_prompt += "Your overarching task is:\n"
            stage_prompt += f"Title: {initial_task.get('title')}\n"
            stage_prompt += f"Description: {initial_task.get('description')}\n\n"
            
            stage_prompt += (
                "Please perform the necessary actions for THIS specific stage only. "
                "Output your results clearly so the next stage can use them."
            )
            
            # Construct the sub-task
            stage_task = {
                "title": f"{initial_task.get('title')} - {stage.display_name}",
                "description": stage_prompt
            }
            
            # Execute the stage
            result = await self.runtime.execute(snapshot, stage_task, context)
            
            if result.status == "failed" or result.status == "timed_out" or result.status == "cancelled":
                logger.error(f"Pipeline failed at stage {stage.stage_id}: {result.error}")
                return {
                    "status": "failed",
                    "failed_stage": stage.stage_id,
                    "error": result.error,
                    "stage_outputs": stage_outputs
                }
                
            # Save the output for the next stage
            stage_outputs[stage.stage_id] = result.output
            
        logger.info(f"Pipeline {pipeline.pipeline_id} completed successfully.")
        
        return {
            "status": "completed",
            "stage_outputs": stage_outputs,
            "final_output": stage_outputs.get(stages[-1].stage_id) if stages else None
        }
