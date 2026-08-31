"""
Base LLM Provider Abstraction.
Defines the standard interface for all Language Model providers.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseLLMProvider(ABC):
    """
    Abstract interface for interacting with Language Models.
    """

    @abstractmethod
    async def chat_completion(
        self, 
        model: str, 
        messages: List[Dict[str, str]], 
        **kwargs: Any
    ) -> Any:
        """
        Executes a chat completion request.
        
        Args:
            model: The name of the model to use.
            messages: A list of message dictionaries (role, content).
            **kwargs: Additional parameters like temperature, max_tokens.
            
        Returns:
            The completion response object (or dictionary).
        """
        pass
