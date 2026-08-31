from typing import Dict, List, Optional
from tools.base import BaseTool
from tools.models import ToolDefinition, ToolNotFoundError

class ToolRegistry:
    """
    In-memory registry of all available tools in the platform.
    """
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """Registers a tool implementation."""
        definition = tool.definition
        if definition.id in self._tools:
            # We could implement versioning here, but for now we just overwrite or log
            pass
        self._tools[definition.id] = tool

    def unregister(self, tool_id: str) -> None:
        if tool_id in self._tools:
            del self._tools[tool_id]

    def get_definition(self, tool_id: str) -> ToolDefinition:
        if tool_id not in self._tools:
            raise ToolNotFoundError(f"Tool {tool_id} not found in registry", tool_id)
        return self._tools[tool_id].definition

    def get_implementation(self, tool_id: str) -> BaseTool:
        if tool_id not in self._tools:
            raise ToolNotFoundError(f"Tool {tool_id} not found in registry", tool_id)
        return self._tools[tool_id]

    def resolve_employee_tools(self, requested_tool_ids: List[str]) -> List[ToolDefinition]:
        """
        Given a list of tool IDs (from an Employee Definition), 
        return their full definitions, filtering out unavailable ones.
        """
        resolved = []
        for tid in requested_tool_ids:
            try:
                definition = self.get_definition(tid)
                if definition.enabled:
                    resolved.append(definition)
            except ToolNotFoundError:
                continue
        return resolved
        
    def list_all_definitions(self) -> List[ToolDefinition]:
        """Returns definitions of all registered tools."""
        return [tool.definition for tool in self._tools.values()]

# Global registry instance
registry = ToolRegistry()
