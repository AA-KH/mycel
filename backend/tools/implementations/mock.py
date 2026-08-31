from typing import Dict, Any
from ..base import BaseTool
from ..context import ToolExecutionContext
from ..models import ToolDefinition
from agents.runtime.result import ToolResult

class MockSuccessTool(BaseTool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            id="mock.success",
            name="Mock Success",
            category="system",
            description="Always succeeds. For testing.",
            input_schema={"type": "object"},
            output_schema={"type": "object"},
            idempotent=True
        )

    async def execute(self, arguments: Dict[str, Any], context: ToolExecutionContext) -> ToolResult:
        return ToolResult(
            tool_name="mock.success",
            status="success",
            output={"message": "Mock executed successfully", "echo": arguments}
        )

class MockErrorTool(BaseTool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            id="mock.error",
            name="Mock Error",
            category="system",
            description="Always fails. For testing.",
            input_schema={"type": "object"},
            output_schema={"type": "object"},
            idempotent=True
        )

    async def execute(self, arguments: Dict[str, Any], context: ToolExecutionContext) -> ToolResult:
        from ..models import ToolExecutionError
        raise ToolExecutionError("Mock error triggered.", tool_id="mock.error")
