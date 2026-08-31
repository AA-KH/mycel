from abc import ABC, abstractmethod
from typing import Dict, Any

class ReasoningEngine(ABC):
    @abstractmethod
    async def reason(self, task: Dict[str, Any], employee_context: Dict[str, Any], reasoning_profile: Dict[str, Any], current_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes reasoning and returns a structured output.
        E.g.,
        {
            "goal": "...",
            "plan": [...],
            "action": "...", # 'tool_call' or 'final_answer'
            "tool_request": {...}, # if action == 'tool_call'
            "final_answer": {...} # if action == 'final_answer'
        }
        """
        pass
