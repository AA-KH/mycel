from typing import Dict, Any, Optional
import asyncio
from datetime import datetime, timezone

from .context import ExecutionContext
from .state import RuntimeState, InvalidStateTransitionError
from .snapshot import ExecutionSnapshot
from .result import ExecutionResult, ToolRequest, ToolResult, VerificationResult
from .interfaces import ToolGateway, ResultVerifier, MemoryProvider, ArtifactManager
from .errors import ExecutionError, ExecutionCancelledError, ExecutionTimeoutError, ToolExecutionError
from .instruction_builder import InstructionBuilder
from .executor import Executor
from .events import RuntimeEventPublisher
from execution.llm.provider import LLMProvider

from core.logger import logger

class AgentRuntime:
    """
    The canonical Agent Runtime.
    Executes an Employee Definition against a Task, moving through the RuntimeState lifecycle.
    """
    
    def __init__(
        self,
        tool_gateway: ToolGateway,
        result_verifier: ResultVerifier,
        memory_provider: MemoryProvider,
        artifact_manager: ArtifactManager,
        max_tool_iterations: int = 10,
        execution_timeout_seconds: int = 300
    ):
        self.tool_gateway = tool_gateway
        self.result_verifier = result_verifier
        self.memory_provider = memory_provider
        self.artifact_manager = artifact_manager
        
        self.max_tool_iterations = max_tool_iterations
        self.execution_timeout_seconds = execution_timeout_seconds
        
        self._state = RuntimeState.CREATED
        self._is_cancelled = False
        
        # We store history here. In a real system this would sync to MongoDB.
        self.history = []
        self.metrics = {
            "llm_calls": 0,
            "tool_calls": 0,
            "duration_ms": 0
        }

    async def _transition_to(self, new_state: RuntimeState, context: ExecutionContext, summary: str = ""):
        if not self._state.can_transition_to(new_state):
            raise InvalidStateTransitionError(self._state, new_state)
        self._state = new_state
        logger.info(f"Runtime transition: {self._state.value}")
        
        # In a real system, we emit the state change
        await RuntimeEventPublisher.publish_state_change(
            execution_id=context.execution_id,
            task_id=context.task_id,
            employee_id=context.employee_id,
            company_id=context.company_id,
            new_state=self._state.value,
            summary=summary,
            user_id=context.user_id
        )
        
    def cancel(self):
        """Cooperatively cancels execution."""
        self._is_cancelled = True

    async def execute(self, snapshot: ExecutionSnapshot, task: Dict[str, Any], context: ExecutionContext) -> ExecutionResult:
        """
        Main entry point for executing a task with an employee snapshot.
        """
        self._state = RuntimeState.CREATED
        self._is_cancelled = False
        start_time = datetime.now(timezone.utc)
        
        # Enclose the actual execution in a timeout and retry boundary where appropriate
        try:
            result = await Executor.with_timeout(
                lambda: self._execute_lifecycle(snapshot, task, context),
                timeout_seconds=self.execution_timeout_seconds,
                error_message=f"Execution {context.execution_id} timed out."
            )
        except ExecutionTimeoutError as e:
            await self._transition_to(RuntimeState.TIMED_OUT, context, "Execution timed out")
            result = self._build_failed_result(context, str(e), start_time)
        except ExecutionCancelledError as e:
            await self._transition_to(RuntimeState.CANCELLED, context, "Execution cancelled")
            result = self._build_failed_result(context, str(e), start_time)
        except Exception as e:
            await self._transition_to(RuntimeState.FAILED, context, f"Execution failed: {e}")
            result = self._build_failed_result(context, str(e), start_time)
            
        await RuntimeEventPublisher.publish_completion(context.execution_id, result)
        return result

    async def _execute_lifecycle(self, snapshot: ExecutionSnapshot, task: Dict[str, Any], exec_context: ExecutionContext) -> ExecutionResult:
        await self._transition_to(RuntimeState.INITIALIZING, exec_context, "Initializing agent runtime")
        
        # Build System Prompt
        system_prompt = InstructionBuilder.build_system_prompt(snapshot, task)
        
        from execution.reasoning.engine import ReasoningEngine
        from execution.reasoning.context import ReasoningContext
        from execution.reasoning.state import ReasoningState
        from execution.reasoning.models import Observation
        
        # Determine strategy from snapshot
        # Fallback to general_problem_solving if not provided
        strategy_name = getattr(snapshot, "reasoning_profile_id", "general_problem_solving")
        team_id = getattr(snapshot, "team_id", None)
        reasoning_engine = ReasoningEngine(reasoning_profile=strategy_name, team_id=team_id)
        
        reasoning_ctx = ReasoningContext(
            execution_id=exec_context.execution_id,
            task_id=exec_context.task_id,
            employee_id=exec_context.employee_id
        )
        
        current_reasoning_state = ReasoningState.INITIALIZING
        
        tool_iterations = 0
        engine_cycles = 0
        final_output = None
        
        while tool_iterations < self.max_tool_iterations and engine_cycles < (self.max_tool_iterations * 5):
            if self._is_cancelled:
                raise ExecutionCancelledError("Execution was cancelled")
                
            engine_cycles += 1
            
            # Drive reasoning
            decision = await reasoning_engine.advance(reasoning_ctx, task, system_prompt, current_reasoning_state)
            current_reasoning_state = decision.get("next_state", current_reasoning_state)
            
            action = decision.get("action")
            details = decision.get("details", {})
            
            # Map ReasoningState back to AgentRuntime state for observability
            if current_reasoning_state in (ReasoningState.PLANNING, ReasoningState.DECOMPOSING):
                await self._transition_to(RuntimeState.PLANNING, exec_context, "Planning task execution")
            elif current_reasoning_state in (ReasoningState.EXECUTING, ReasoningState.READY):
                await self._transition_to(RuntimeState.EXECUTING, exec_context, f"Executing (iteration {tool_iterations+1})")
                
            if action == "final_answer" or action == "complete":
                final_output = details
                break
                
            elif action == "tool_call":
                await self._transition_to(RuntimeState.WAITING_TOOL, exec_context, f"Using tool: {details.get('tool_name', 'unknown')}")
                
                tool_name = details.get("tool_name")
                arguments = details.get("arguments", {})
                
                # Check permissions
                if tool_name not in snapshot.tools:
                    raise ExecutionError(f"Permission denied: Tool {tool_name} is not declared by employee.", exec_context.execution_id)
                
                tool_req = ToolRequest(
                    execution_id=exec_context.execution_id,
                    employee_id=exec_context.employee_id,
                    tool_name=tool_name,
                    arguments=arguments,
                    reason=details.get("reason", "Requested by reasoning engine")
                )
                
                try:
                    tool_result = await self.tool_gateway.execute(tool_req)
                    self.metrics["tool_calls"] += 1
                    
                    await self._transition_to(RuntimeState.OBSERVING, exec_context, "Observing tool result")
                    status_value = "failed" if tool_result.status == "error" else "success"
                    summary_text = f"Tool {tool_name} failed: {tool_result.error}" if tool_result.status == "error" else f"Tool {tool_name} returned data"
                    
                    obs_data = {"output": tool_result.output}
                    if tool_result.error:
                        obs_data["error"] = tool_result.error

                    obs = Observation(
                        step_id="unknown",
                        type="tool_result",
                        status=status_value,
                        summary=summary_text,
                        data=obs_data
                    )
                    reasoning_ctx.add_observation(obs)
                    current_reasoning_state = ReasoningState.OBSERVING
                    
                except Exception as e:
                    logger.error(f"Tool execution failed during agent loop: {tool_name} -> {str(e)}")
                    obs = Observation(
                        step_id="unknown",
                        type="tool_result",
                        status="failed",
                        summary=f"Tool {tool_name} failed: {str(e)}"
                    )
                    reasoning_ctx.add_observation(obs)
                    current_reasoning_state = ReasoningState.OBSERVING
                    
                tool_iterations += 1
                    
            elif action == "blocked":
                raise ExecutionError(f"Reasoning blocked: {details.get('reason')}", exec_context.execution_id)
            
        if not final_output:
            raise ExecutionError("Max tool iterations reached without final answer.", exec_context.execution_id)
            
        await self._transition_to(RuntimeState.VERIFYING, exec_context, "Verifying output")
        
        verification = await self.result_verifier.verify(task, final_output, task.get("expected_output", {}))
        
        if verification.status == "failed":
            await self._transition_to(RuntimeState.FAILED, exec_context, f"Verification failed: {verification.reason}")
            raise ExecutionError(f"Verification failed: {verification.reason}", exec_context.execution_id)
            
        await self._transition_to(RuntimeState.COMPLETED, exec_context, "Task completed successfully")
        
        end_time = datetime.now(timezone.utc)
        self.metrics["duration_ms"] = int((end_time - exec_context.created_at).total_seconds() * 1000)
        
        return ExecutionResult(
            execution_id=exec_context.execution_id,
            employee_id=exec_context.employee_id,
            task_id=exec_context.task_id,
            status=self._state.value.lower(),
            output=final_output,
            verification=verification,
            metrics=self.metrics,
            completed_at=end_time
        )
        
    def _build_failed_result(self, context: ExecutionContext, error_str: str, start_time: datetime) -> ExecutionResult:
        end_time = datetime.now(timezone.utc)
        self.metrics["duration_ms"] = int((end_time - start_time).total_seconds() * 1000)
        return ExecutionResult(
            execution_id=context.execution_id,
            employee_id=context.employee_id,
            task_id=context.task_id,
            status=self._state.value.lower(),
            output={},
            verification=VerificationResult(status="failed", reason=error_str),
            metrics=self.metrics,
            error=error_str,
            completed_at=end_time
        )
