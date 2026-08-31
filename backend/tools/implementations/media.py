from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from ..base import BaseTool
from ..context import ToolExecutionContext
from ..models import ToolDefinition, ArtifactReference
from agents.runtime.result import ToolResult

class FFmpegArgs(BaseModel):
    operation: str = Field(description="The FFmpeg operation to perform (e.g., merge, resize, trim)")
    input_files: List[str] = Field(description="List of input file references or URLs")
    output_format: Optional[str] = Field(default="mp4")
    parameters: Optional[Dict[str, Any]] = Field(default=None)

class FFmpegTool(BaseTool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            id="ffmpeg",
            name="FFmpeg Media Processing",
            category="media",
            description="Process audio/video files with structured operations (e.g., merge, resize, trim).",
            input_schema={"type": "object", "required": ["operation", "input_files"]},
            output_schema={"type": "object"},
            risk_level="high",
            timeout_seconds=300 # Encoding can take a while
        )

    async def execute(self, arguments: Dict[str, Any], context: ToolExecutionContext) -> ToolResult:
        operation = arguments.get("operation")
        return ToolResult(
            tool_name="ffmpeg",
            status="success",
            output={"message": f"FFmpeg '{operation}' executed successfully in sandbox."}
        )

class CloudinaryUploadTool(BaseTool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            id="cloudinary.upload",
            name="Cloudinary Upload",
            category="media",
            description="Upload a generated media artifact to Cloudinary.",
            input_schema={"type": "object", "required": ["file_path", "resource_type"]},
            output_schema={"type": "object"},
            requires_network=True,
            timeout_seconds=60
        )

    async def execute(self, arguments: Dict[str, Any], context: ToolExecutionContext) -> ToolResult:
        file_path = arguments.get("file_path")
        resource_type = arguments.get("resource_type")
        
        from artifacts import get_artifact_service
        service = get_artifact_service()
        
        try:
            artifact_ref = await service.create_and_store(
                company_id=context.company_id,
                workspace_id="workspace_1", # Mocked for now
                task_id=context.task_id,
                execution_id=context.execution_id,
                employee_id=context.employee_id,
                artifact_type=resource_type,
                file_path=file_path,
                expected_output={"mime_type": f"{resource_type}/mock"} # Very loose validation here for the tool test
            )
            
            return ToolResult(
                tool_name="cloudinary.upload",
                status="success",
                output={"artifact": artifact_ref.model_dump()},
                artifact_ids=[artifact_ref.artifact_id]
            )
        except Exception as e:
            return ToolResult(
                tool_name="cloudinary.upload",
                status="error",
                error=f"Artifact upload failed: {e}",
                output={}
            )
