import asyncio
from typing import ClassVar, Type, Any, Dict
from pydantic import BaseModel, Field

from ..models import ToolDefinition
from ..context import ToolExecutionContext as ToolContext
from ..providers.manim import get_manim_provider
from artifacts.storage import get_storage_provider

class CreativeTechnicalAnimationArgs(BaseModel):
    manim_code: str = Field(..., description="The Manim Python code to render the technical animation.")
    scene_class: str = Field(default="Scene1", description="The name of the Scene class to render.")
    resolution: str = Field(default="720p", description="Resolution of the animation.")

from ..base import BaseTool
from agents.runtime.result import ToolResult

class CreativeTechnicalAnimationTool(BaseTool):
    """
    Tool for rendering technical animations using Manim.
    Surfaces the Manim capability to creative specialists.
    """
    
    def __init__(self):
        super().__init__()
        self.provider = get_manim_provider()

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            id="creative.technical_animation.render",
            name="Manim Technical Animation",
            category="media",
            description="Render technical animations using Manim code to a video artifact.",
            input_schema=CreativeTechnicalAnimationArgs.model_json_schema(),
            output_schema={"type": "object"},
            timeout_seconds=300
        )
        
    async def execute(self, arguments: Dict[str, Any], context: ToolContext) -> ToolResult:
        """Execute the technical animation rendering."""
        
        args = CreativeTechnicalAnimationArgs(**arguments)
        
        video_bytes = await self.provider.render(
            code=args.manim_code,
            scene_class=args.scene_class,
            resolution=args.resolution
        )
        
        # Save to artifact storage
        storage = get_storage_provider()
        artifact_id = storage.save_artifact(
            task_id=context.task_id or "default",
            data=video_bytes,
            filename=f"manim_render_{args.scene_class}.mp4",
            content_type="video/mp4"
        )
        
        artifact_url = storage.get_artifact_url(artifact_id, context.task_id or "default")
        
        return ToolResult(
            tool_name=self.definition.id,
            status="success",
            output={
                "artifact_id": artifact_id,
                "artifact_url": artifact_url,
                "message": "Technical animation rendered successfully."
            }
        )
        

