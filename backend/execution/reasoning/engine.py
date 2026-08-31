from typing import Dict, Any, Optional
from .context import ReasoningContext
from .state import ReasoningState
from .llm_adapter import LLMReasoner
from .strategies import get_strategy
from .models import ReasoningResult
import logging

logger = logging.getLogger(__name__)

class ReasoningEngine:
    """
    Drives the Reasoning lifecycle for an Employee's task execution.
    It doesn't execute tools; it decides what tools to execute and evaluates the results.
    """
    def __init__(self, reasoning_profile: str, max_retries: int = 3, team_id: Optional[str] = None):
        self.llm = LLMReasoner(max_retries=max_retries, team_id=team_id)
        self.strategy = get_strategy(reasoning_profile, self.llm)
        self.reasoning_profile = reasoning_profile
        self.team_id = team_id

    async def advance(self, context: ReasoningContext, task: Dict[str, Any], system_prompt: str, current_state: ReasoningState) -> Dict[str, Any]:
        """
        Advances the reasoning state machine until it either produces a final answer, 
        requests a tool execution, or fails/blocks.
        Returns a dict: {"action": "...", "details": {...}, "next_state": ReasoningState, "context": context}
        """
        try:
            if current_state == ReasoningState.INITIALIZING:
                # Understand the task
                context.intent = await self.strategy.understand(task, context, system_prompt)
                return {"action": "continue", "next_state": ReasoningState.PLANNING, "context": context}

            elif current_state == ReasoningState.PLANNING:
                # Decompose and create a plan
                context.plan = await self.strategy.decompose_and_plan(context.intent, context, system_prompt)
                return {"action": "continue", "next_state": ReasoningState.READY, "context": context}

            elif current_state == ReasoningState.READY or current_state == ReasoningState.EXECUTING:
                # Decide the next tool or if we are done
                decision = await self.strategy.decide_next_action(context, system_prompt)
                if decision.get("action") == "final_answer":
                    return {"action": "final_answer", "details": decision.get("details"), "next_state": ReasoningState.VERIFYING, "context": context}
                elif decision.get("action") == "tool_call":
                    return {"action": "tool_call", "details": decision.get("details"), "next_state": ReasoningState.EXECUTING, "context": context}
                else:
                    # Fallback if strategy returns something weird
                    return {"action": "blocked", "details": {"reason": "Unknown action type"}, "next_state": ReasoningState.BLOCKED, "context": context}

            elif current_state == ReasoningState.OBSERVING:
                # We just got a tool observation back (which was added to context by Runtime)
                critique = await self.strategy.critique(context, system_prompt)
                context.critiques.append(critique)
                
                if critique.status == "needs_revision":
                    return {"action": "continue", "next_state": ReasoningState.REVISING, "context": context}
                elif critique.status == "blocked":
                    return {"action": "blocked", "details": {"reason": critique.recommended_action}, "next_state": ReasoningState.BLOCKED, "context": context}
                else:
                    return {"action": "continue", "next_state": ReasoningState.READY, "context": context}

            elif current_state == ReasoningState.REVISING:
                # Simple revision: just try again with the new critique in context
                return {"action": "continue", "next_state": ReasoningState.READY, "context": context}

            elif current_state == ReasoningState.VERIFYING:
                # Runtime passes final_output in the task dict for verification
                final_output = task.get("final_output", {})
                passed = await self.strategy.verify(final_output, context, system_prompt)
                if passed:
                    return {"action": "complete", "details": final_output, "next_state": ReasoningState.COMPLETED, "context": context}
                else:
                    # If verification fails, go back to planning or ready
                    return {"action": "continue", "next_state": ReasoningState.CRITIQUING, "context": context}

            else:
                return {"action": "blocked", "details": {"reason": f"Unhandled state {current_state}"}, "next_state": ReasoningState.BLOCKED, "context": context}

        except Exception as e:
            logger.error(f"Reasoning Engine failed at {current_state}: {e}")
            return {"action": "failed", "details": {"error": str(e)}, "next_state": ReasoningState.FAILED, "context": context}
