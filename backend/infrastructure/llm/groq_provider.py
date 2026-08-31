"""
Groq LLM Provider Implementation.
Wraps the GroqEngineManager to adhere to the BaseLLMProvider interface
with optional team-level API key routing.
"""

from typing import Any, Dict, List, Optional
from core.groq_engine import engine_manager
from .base import BaseLLMProvider


class GroqProvider(BaseLLMProvider):
    """
    Implementation of the LLM Provider for Groq.
    Routes calls through the GroqEngineManager for automatic per-team
    failover and rate-limit handling.
    """

    def __init__(self, team_id: Optional[str] = None):
        self.team_id = team_id

    async def chat_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        **kwargs: Any,
    ) -> Any:
        """
        Delegates the completion request to the team-aware Groq engine manager.
        Pass team_id at construction time to route to a dedicated key pool.
        """
        return await engine_manager.chat_completion(
            model=model,
            messages=messages,
            team_id=self.team_id,
            **kwargs,
        )


# Global default instance for dependency injection (uses global key pool)
llm_provider = GroqProvider()
