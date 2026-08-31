from abc import ABC, abstractmethod
from typing import Dict, Any, List

from ..models import TaskIntent, Plan, Observation, Critique
from ..context import ReasoningContext
from ..llm_adapter import LLMReasoner

class ReasoningStrategy(ABC):
    """
    Base interface for all reasoning strategies.
    Strategies define HOW an agent thinks through a task.
    """
    def __init__(self, llm: LLMReasoner):
        self.llm = llm

    @abstractmethod
    async def understand(self, task: Dict[str, Any], context: ReasoningContext, system_prompt: str) -> TaskIntent:
        """Extracts constraints, goals, and success criteria."""
        pass

    @abstractmethod
    async def decompose_and_plan(self, intent: TaskIntent, context: ReasoningContext, system_prompt: str) -> Plan:
        """Breaks down the intent into a dependency graph of PlanNodes."""
        pass

    @abstractmethod
    async def decide_next_action(self, context: ReasoningContext, system_prompt: str) -> Dict[str, Any]:
        """
        Given the current plan and observations, decides what to do next.
        Returns {"action": "tool_call", "details": {...}} or {"action": "final_answer", "details": {...}}
        """
        pass

    @abstractmethod
    async def critique(self, context: ReasoningContext, system_prompt: str) -> Critique:
        """Evaluates recent observations to see if the plan is working."""
        pass

    @abstractmethod
    async def verify(self, final_output: Dict[str, Any], context: ReasoningContext, system_prompt: str) -> bool:
        """Determines if the final output actually satisfies the TaskIntent."""
        pass
