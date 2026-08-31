from typing import Dict, Any
from .base import ReasoningStrategy
from ..models import TaskIntent, Plan, Critique
from ..context import ReasoningContext

class GeneralReasoningStrategy(ReasoningStrategy):
    """
    A standard step-by-step reasoning profile suitable for generic tasks.
    """
    
    async def understand(self, task: Dict[str, Any], context: ReasoningContext, system_prompt: str) -> TaskIntent:
        prompt = f"Task: {task.get('description', '')}\nExpected Output: {task.get('expected_output', {})}\n\nPlease normalize this task into a TaskIntent."
        return await self.llm.generate_structured(system_prompt, prompt, TaskIntent)

    async def decompose_and_plan(self, intent: TaskIntent, context: ReasoningContext, system_prompt: str) -> Plan:
        prompt = f"Goal: {intent.goal}\nConstraints: {intent.constraints}\nDependencies: {intent.dependencies}\n\nCreate a structured execution plan."
        return await self.llm.generate_structured(system_prompt, prompt, Plan)

    async def decide_next_action(self, context: ReasoningContext, system_prompt: str) -> Dict[str, Any]:
        from pydantic import BaseModel
        from typing import Literal
        class NextAction(BaseModel):
            action: Literal["tool_call", "final_answer"]
            details: Dict[str, Any]
            
        prompt = f"{context.to_llm_context()}\nWhat is the next logical step according to the plan? You MUST set action to 'tool_call' if you need to use a tool, or 'final_answer' if you have completed the task. If action is 'tool_call', 'details' MUST contain 'tool_name' and 'arguments'."
        result = await self.llm.generate_structured(system_prompt, prompt, NextAction)
        return {"action": result.action, "details": result.details}

    async def critique(self, context: ReasoningContext, system_prompt: str) -> Critique:
        prompt = f"{context.to_llm_context()}\nEvaluate the recent observations. Are we making progress? Are there errors?"
        return await self.llm.generate_structured(system_prompt, prompt, Critique)

    async def verify(self, final_output: Dict[str, Any], context: ReasoningContext, system_prompt: str) -> bool:
        from pydantic import BaseModel
        class Verification(BaseModel):
            passed: bool
            reasoning: str
            
        prompt = f"Goal: {context.intent.goal if context.intent else 'Unknown'}\nOutput: {final_output}\n\nDoes this output satisfy the goal completely?"
        res = await self.llm.generate_structured(system_prompt, prompt, Verification)
        return res.passed
