import logging
import uuid
from typing import Dict, Any, Optional, List

from tasks.models import TaskRequest, TaskContext, TaskPriority
from tasks.orchestrator import TaskOrchestrator
from domains.company_builder.models import CompanyBuilderState, BuilderStage, PipelineStatus
from domains.company_builder.memory_bridge import CompanyMemoryBridge
import asyncio

logger = logging.getLogger(__name__)

class CompanyBuilderPipeline:
    """
    Stateful workflow engine for the Autonomous Company Builder demonstration.
    """
    def __init__(self, memory_bridge: CompanyMemoryBridge, orchestrator: TaskOrchestrator):
        self._memory = memory_bridge
        self._orchestrator = orchestrator
        self._active_workflows: Dict[str, CompanyBuilderState] = {}

    async def initialize_company(self, company_id: str, workspace_id: str) -> CompanyBuilderState:
        """Starts a new company building workflow."""
        state = CompanyBuilderState(
            company_id=company_id,
            workspace_id=workspace_id,
            current_stage=BuilderStage.COMPANY_INITIALIZATION,
            status=PipelineStatus.IN_PROGRESS
        )
        self._active_workflows[state.workflow_id] = state
        logger.info(f"Initialized Company Builder Workflow: {state.workflow_id} for Company: {company_id}")
        
        # Publish init event
        try:
            from core.rabbitmq import rabbitmq_producer
            await rabbitmq_producer.publish(f"company_builder.{state.workflow_id}.init", state.model_dump(mode="json"))
        except Exception as e:
            logger.warning(f"Failed to publish init event: {e}")
            
        # Move to discovery stage
        await self.advance_stage(state.workflow_id, BuilderStage.REQUIREMENTS_DISCOVERY)
        return state

    def get_state(self, workflow_id: str) -> Optional[CompanyBuilderState]:
        return self._active_workflows.get(workflow_id)

    async def advance_stage(self, workflow_id: str, next_stage: BuilderStage):
        state = self.get_state(workflow_id)
        if not state:
            raise ValueError(f"Workflow {workflow_id} not found.")

        if state.current_stage:
            state.completed_stages.append(state.current_stage)
            
        if next_stage in state.pending_stages:
            state.pending_stages.remove(next_stage)
            
        state.current_stage = next_stage
        logger.info(f"Workflow {workflow_id} advanced to stage: {next_stage}")
        
        try:
            from core.rabbitmq import rabbitmq_producer
            await rabbitmq_producer.publish(f"company_builder.{state.workflow_id}.stage_changed", {"new_stage": next_stage.value})
        except Exception as e:
            logger.warning(f"Failed to publish stage_changed event: {e}")

    async def process_prompt(self, workflow_id: str, prompt: str) -> Dict[str, Any]:
        """
        Receives a user prompt, retrieves historical constraints from memory,
        and dispatches it via the TaskOrchestrator to automatically resolve teams.
        """
        state = self.get_state(workflow_id)
        if not state:
            raise ValueError(f"Workflow {workflow_id} not found.")
            
        company_id = state.company_id
        
        # 1. Build unified context from memory
        current_artifacts = list(state.artifacts.values())
        task_context = self._memory.build_task_context(
            company_id=company_id,
            prompt=prompt,
            current_artifacts=current_artifacts
        )
        
        # Stage specific orchestration
        if state.current_stage == BuilderStage.FEASIBILITY_ANALYSIS:
            return self._execute_feasibility(state, prompt, task_context)
            
        if state.current_stage == BuilderStage.GROWTH_STRATEGY:
            return self._execute_growth_strategy(state, prompt, task_context)
            
        if state.current_stage == BuilderStage.BRAND_IDENTITY:
            return self._execute_brand_identity(state, prompt, task_context)
            
        if state.current_stage == BuilderStage.LOGO_CREATION:
            return self._execute_logo_creation(state, prompt, task_context)
            
        if state.current_stage == BuilderStage.POSTER_CREATION:
            return self._execute_poster_creation(state, prompt, task_context)
            
        if state.current_stage == BuilderStage.WEBSITE_CREATION:
            return self._execute_website_creation(state, prompt, task_context)
            
        if state.current_stage == BuilderStage.PITCH_DECK_CREATION:
            return self._execute_pitch_deck_creation(state, prompt, task_context)
        
        # Default behavior: single task orchestration
        stage_directive = f"Current Pipeline Stage: {state.current_stage.value}. "
        full_prompt = stage_directive + prompt
        
        logger.info(f"Dispatching task for stage {state.current_stage.value} with prompt: {prompt}")
        
        orchestration_result = self._orchestrator.orchestrate_task(
            user_input=full_prompt,
            organization_id=company_id,
            context=task_context
        )
        
        state.tasks.append(orchestration_result.task_id)
        
        return {
            "workflow_id": workflow_id,
            "stage": state.current_stage,
            "orchestration_result": orchestration_result.model_dump()
        }
        
    def _execute_feasibility(self, state: CompanyBuilderState, prompt: str, task_context: TaskContext) -> Dict[str, Any]:
        """
        Orchestrates parallel research, legal, and financial feasibility tasks.
        """
        # We explicitly dispatch three distinct tasks
        tasks_to_launch = [
            f"Conduct market research and demographic feasibility for: {prompt}",
            f"Analyze legal requirements, compliance risks, and regulatory feasibility for: {prompt}",
            f"Determine financial feasibility, projected costs, and funding requirements for: {prompt}"
        ]
        
        results = []
        for t_prompt in tasks_to_launch:
            res = self._orchestrator.orchestrate_task(
                user_input=t_prompt,
                organization_id=state.company_id,
                context=task_context
            )
            state.tasks.append(res.task_id)
            results.append(res.model_dump())
            
        # Dispatch Synthesizer Task
        synth_res = self._orchestrator.orchestrate_task(
            user_input=f"Synthesize the research, legal, and financial feasibility analyses into a unified Feasibility Report for: {prompt}",
            organization_id=state.company_id,
            context=task_context
        )
        state.tasks.append(synth_res.task_id)
            
        return {
            "workflow_id": state.workflow_id,
            "stage": state.current_stage,
            "sub_tasks_orchestrated": len(results),
            "orchestration_results": results,
            "synthesizer_result": synth_res.model_dump()
        }

    def _execute_growth_strategy(self, state: CompanyBuilderState, prompt: str, task_context: TaskContext) -> Dict[str, Any]:
        """
        Orchestrates the growth strategy based on the prior feasibility results.
        """
        full_prompt = f"Using the recent feasibility analysis, create a comprehensive Growth Strategy for: {prompt}"
        res = self._orchestrator.orchestrate_task(user_input=full_prompt, organization_id=state.company_id, context=task_context)
        state.tasks.append(res.task_id)
        return {"workflow_id": state.workflow_id, "stage": state.current_stage, "orchestration_result": res.model_dump()}

    def _execute_brand_identity(self, state: CompanyBuilderState, prompt: str, task_context: TaskContext) -> Dict[str, Any]:
        full_prompt = f"Define the visual brand identity, color palette, and tone of voice for: {prompt}"
        res = self._orchestrator.orchestrate_task(user_input=full_prompt, organization_id=state.company_id, context=task_context)
        state.tasks.append(res.task_id)
        return {"workflow_id": state.workflow_id, "stage": state.current_stage, "orchestration_result": res.model_dump()}

    def _execute_logo_creation(self, state: CompanyBuilderState, prompt: str, task_context: TaskContext) -> Dict[str, Any]:
        full_prompt = f"Generate a high-quality logo design incorporating the established brand identity for: {prompt}"
        res = self._orchestrator.orchestrate_task(user_input=full_prompt, organization_id=state.company_id, context=task_context)
        state.tasks.append(res.task_id)
        return {"workflow_id": state.workflow_id, "stage": state.current_stage, "orchestration_result": res.model_dump()}

    def _execute_poster_creation(self, state: CompanyBuilderState, prompt: str, task_context: TaskContext) -> Dict[str, Any]:
        full_prompt = f"Generate a promotional poster or marketing asset based on the brand identity for: {prompt}"
        res = self._orchestrator.orchestrate_task(user_input=full_prompt, organization_id=state.company_id, context=task_context)
        state.tasks.append(res.task_id)
        return {"workflow_id": state.workflow_id, "stage": state.current_stage, "orchestration_result": res.model_dump()}

    def _execute_website_creation(self, state: CompanyBuilderState, prompt: str, task_context: TaskContext) -> Dict[str, Any]:
        full_prompt = f"Create the HTML/CSS code for a responsive landing page using the generated brand assets for: {prompt}"
        res = self._orchestrator.orchestrate_task(user_input=full_prompt, organization_id=state.company_id, context=task_context)
        state.tasks.append(res.task_id)
        return {"workflow_id": state.workflow_id, "stage": state.current_stage, "orchestration_result": res.model_dump()}

    def _execute_pitch_deck_creation(self, state: CompanyBuilderState, prompt: str, task_context: TaskContext) -> Dict[str, Any]:
        full_prompt = f"Synthesize all artifacts (growth strategy, brand, feasibility) into a final Pitch Deck for: {prompt}"
        res = self._orchestrator.orchestrate_task(user_input=full_prompt, organization_id=state.company_id, context=task_context)
        state.tasks.append(res.task_id)
        return {"workflow_id": state.workflow_id, "stage": state.current_stage, "orchestration_result": res.model_dump()}
