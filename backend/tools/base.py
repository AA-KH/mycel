from abc import ABC, abstractmethod
from typing import Dict, Any

from .models import ToolDefinition
from agents.runtime.result import ToolResult
from .context import ToolExecutionContext

class BaseTool(ABC):
    """
    The implementation contract for any Tool in the platform.
    """
    @property
    @abstractmethod
    def definition(self) -> ToolDefinition:
        """Returns the canonical ToolDefinition for this tool."""
        pass

    @abstractmethod
    async def execute(self, arguments: Dict[str, Any], context: ToolExecutionContext) -> ToolResult:
        """
        Executes the tool with the provided arguments and context.
        Returns a ToolResult.
        """
        pass
