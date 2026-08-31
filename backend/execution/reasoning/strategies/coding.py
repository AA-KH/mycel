from typing import Dict, Any
from .base import ReasoningStrategy
from ..models import TaskIntent, Plan, Critique
from ..context import ReasoningContext

class CodeTestStrategy(ReasoningStrategy):
    """
    Coding-focused workflow: Design -> Implement -> Test -> Revise.
    """
    
    async def understand(self, task: Dict[str, Any], context: ReasoningContext, system_prompt: str) -> TaskIntent:
        system_prompt += "\nYou are approaching this as a Software Engineer. Focus on technical requirements, edge cases, and testing criteria."
        prompt = f"Task: {task.get('description', '')}\n\nNormalize this task into a technical TaskIntent."
        return await self.llm.generate_structured(system_prompt, prompt, TaskIntent)

    async def decompose_and_plan(self, intent: TaskIntent, context: ReasoningContext, system_prompt: str) -> Plan:
        system_prompt += "\nYour plan must include steps for inspecting the environment/existing code, implementation, and automated testing."
        prompt = f"Goal: {intent.goal}\nConstraints: {intent.constraints}\n\nCreate an engineering execution plan."
        return await self.llm.generate_structured(system_prompt, prompt, Plan)

    async def decide_next_action(self, context: ReasoningContext, system_prompt: str) -> Dict[str, Any]:
        from pydantic import BaseModel
        from typing import Literal
        class NextAction(BaseModel):
            action: Literal["tool_call", "final_answer"]
            details: Dict[str, Any]
            
        prompt = f"{context.to_llm_context()}\nWhat is the next logical action? You MUST set action to 'tool_call' if you need to use a tool, or 'final_answer' if you have completed the task. If action is 'tool_call', 'details' MUST contain 'tool_name' and 'arguments'."
        result = await self.llm.generate_structured(system_prompt, prompt, NextAction)
        return {"action": result.action, "details": result.details}

    async def critique(self, context: ReasoningContext, system_prompt: str) -> Critique:
        system_prompt += "\nLook closely at any error logs or test failures in the observations. Determine exactly what code change is needed to fix them."
        prompt = f"{context.to_llm_context()}\nCritique the recent execution results."
        return await self.llm.generate_structured(system_prompt, prompt, Critique)

    async def verify(self, final_output: Dict[str, Any], context: ReasoningContext, system_prompt: str) -> bool:
        from pydantic import BaseModel
        class Verification(BaseModel):
            passed: bool
            reasoning: str
            
        prompt = f"Goal: {context.intent.goal if context.intent else 'Unknown'}\nOutput: {final_output}\n\nDoes this implementation satisfy all technical requirements and pass verification?"
        res = await self.llm.generate_structured(system_prompt, prompt, Verification)
        return res.passed
