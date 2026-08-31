from typing import Dict, Any
from .base import ReasoningStrategy
from ..models import TaskIntent, Plan, Critique
from ..context import ReasoningContext

class ResearchVerifyStrategy(ReasoningStrategy):
    """
    Research-focused workflow: Gather evidence -> Detect conflicts -> Synthesize.
    """
    
    async def understand(self, task: Dict[str, Any], context: ReasoningContext, system_prompt: str) -> TaskIntent:
        system_prompt += "\nYou are approaching this as a Researcher. Identify specific information required to answer the question, and what constitutes reliable evidence."
        prompt = f"Task: {task.get('description', '')}\n\nNormalize this task into a TaskIntent focusing on research requirements."
        return await self.llm.generate_structured(system_prompt, prompt, TaskIntent)

    async def decompose_and_plan(self, intent: TaskIntent, context: ReasoningContext, system_prompt: str) -> Plan:
        system_prompt += "\nYour plan must include steps for finding sources, extracting claims, comparing conflicting data, and final synthesis."
        prompt = f"Goal: {intent.goal}\nConstraints: {intent.constraints}\n\nCreate a research execution plan."
        return await self.llm.generate_structured(system_prompt, prompt, Plan)

    async def decide_next_action(self, context: ReasoningContext, system_prompt: str) -> Dict[str, Any]:
        from pydantic import BaseModel
        from typing import Literal
        class NextAction(BaseModel):
            action: Literal["tool_call", "final_answer"]
            details: Dict[str, Any]
            
        prompt = f"{context.to_llm_context()}\nBased on findings, what is the next action? You MUST set action to 'tool_call' if you need to use a tool, or 'final_answer' if you have completed the task. If action is 'tool_call', 'details' MUST contain 'tool_name' and 'arguments'."
        result = await self.llm.generate_structured(system_prompt, prompt, NextAction)
        return {"action": result.action, "details": result.details}

    async def critique(self, context: ReasoningContext, system_prompt: str) -> Critique:
        system_prompt += "\nEvaluate the sources you've gathered. Are they reliable? Is there a conflict you haven't resolved?"
        prompt = f"{context.to_llm_context()}\nCritique your evidence."
        return await self.llm.generate_structured(system_prompt, prompt, Critique)

    async def verify(self, final_output: Dict[str, Any], context: ReasoningContext, system_prompt: str) -> bool:
        from pydantic import BaseModel
        class Verification(BaseModel):
            passed: bool
            reasoning: str
            
        prompt = f"Goal: {context.intent.goal if context.intent else 'Unknown'}\nOutput: {final_output}\n\nDoes this report answer the core question with sufficient cited evidence?"
        res = await self.llm.generate_structured(system_prompt, prompt, Verification)
        return res.passed
