import os
from pathlib import Path
from typing import Dict, Any

from ..base import BaseTool
from ..context import ToolExecutionContext
from ..models import ToolDefinition, ToolValidationError
from agents.runtime.result import ToolResult

def _get_safe_path(requested_path: str, workspace_id: str) -> Path:
    # Use a mock workspace root for this exercise
    base = Path(f"/tmp/mycel_workspace/{workspace_id}").resolve()
    target = (base / requested_path).resolve()
    
    # Check for path traversal
    if not str(target).startswith(str(base)):
        raise ToolValidationError(f"Path traversal detected. Cannot access {requested_path}", "filesystem")
    return target

class FilesystemReadTool(BaseTool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            id="filesystem.read",
            name="Filesystem Read",
            category="filesystem",
            description="Read a file securely within the workspace.",
            input_schema={"type": "object", "required": ["path"]},
            output_schema={"type": "object"},
            risk_level="low",
            idempotent=True
        )

    async def execute(self, arguments: Dict[str, Any], context: ToolExecutionContext) -> ToolResult:
        try:
            workspace_id = context.workspace_id or context.company_id
            safe_path = _get_safe_path(arguments["path"], workspace_id)
            
            # In a real system, we'd actually read the file. 
            # We'll just return success for mock testing.
            return ToolResult(
                tool_name=self.definition.id,
                status="success",
                output={"content": f"Mock content of {safe_path}"}
            )
        except Exception as e:
            return ToolResult(tool_name=self.definition.id, status="error", output={}, error=str(e))

class FilesystemWriteTool(BaseTool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            id="filesystem.write",
            name="Filesystem Write",
            category="filesystem",
            description="Write a file securely within the workspace.",
            input_schema={"type": "object", "required": ["path", "content"]},
            output_schema={"type": "object"},
            risk_level="medium",
            idempotent=False
        )

    async def execute(self, arguments: Dict[str, Any], context: ToolExecutionContext) -> ToolResult:
        try:
            workspace_id = context.workspace_id or context.company_id
            safe_path = _get_safe_path(arguments["path"], workspace_id)
            
            return ToolResult(
                tool_name=self.definition.id,
                status="success",
                output={"message": f"Successfully wrote to {safe_path}"}
            )
        except Exception as e:
            return ToolResult(tool_name=self.definition.id, status="error", output={}, error=str(e))
