import asyncio
from typing import ClassVar, Type, Any, Dict, List
from pydantic import BaseModel, Field

from ..models import ToolDefinition
from ..context import ToolExecutionContext as ToolContext
from ..providers.stock_media import get_stock_media_provider
from ..providers.tts import get_tts_provider
from artifacts.storage import get_storage_provider
from ..base import BaseTool
from agents.runtime.result import ToolResult

class CreativeStockSearchArgs(BaseModel):
    query: str = Field(..., description="The search query for stock media (e.g., 'abstract tech background').")
    media_type: str = Field(default="video", description="Type of media to search for ('video', 'image').")

class CreativeStockSearchTool(BaseTool):
    """
    Tool for searching and downloading stock media (video/images).
    Uses the external stock provider API and stores results as artifacts.
    """
    def __init__(self):
        super().__init__()
        self.provider = get_stock_media_provider()

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            id="creative.stock_media.search",
            name="Stock Media Search",
            category="media",
            description="Search for and download stock video footage or images based on a query.",
            input_schema=CreativeStockSearchArgs.model_json_schema(),
            output_schema={"type": "object"},
            timeout_seconds=120
        )
        
    async def execute(self, arguments: Dict[str, Any], context: ToolContext) -> ToolResult:
        """Execute the stock media search and download."""
        
        args = CreativeStockSearchArgs(**arguments)
        results = await self.provider.search(query=args.query, media_type=args.media_type)
        if not results:
            return ToolResult(
                tool_name=self.definition.id,
                status="error",
                output={"message": f"No {args.media_type} found for query '{args.query}'."}
            )
            
        # Download the best match
        best_match = results[0]
        media_bytes = await self.provider.download(best_match.url)
        
        # Save to artifact storage
        storage = get_storage_provider()
        artifact_id = storage.save_artifact(
            task_id=context.task_id or "default",
            data=media_bytes,
            filename=f"stock_{args.query.replace(' ', '_')}.mp4",
            content_type="video/mp4"
        )
        
        artifact_url = storage.get_artifact_url(artifact_id, context.task_id or "default")
        
        return ToolResult(
            tool_name=self.definition.id,
            status="success",
            output={
                "artifact_id": artifact_id,
                "artifact_url": artifact_url,
                "message": f"Successfully sourced stock media for query '{args.query}'.",
            }
        )
        
class CreativeSpeechGenerationArgs(BaseModel):
    text: str = Field(..., description="The text to synthesize to speech.")
    voice: str = Field(default="en-US-Standard-A", description="The voice profile to use.")
    
class CreativeSpeechGenerationTool(BaseTool):
    """
    Tool for generating speech (TTS) from text.
    """
    def __init__(self):
        super().__init__()
        self.provider = get_tts_provider()

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            id="creative.speech.generate",
            name="Text to Speech Generation",
            category="media",
            description="Generate TTS audio from text.",
            input_schema=CreativeSpeechGenerationArgs.model_json_schema(),
            output_schema={"type": "object"},
            timeout_seconds=60
        )
        
    async def execute(self, arguments: Dict[str, Any], context: ToolContext) -> ToolResult:
        """Execute TTS generation."""
        args = CreativeSpeechGenerationArgs(**arguments)
        audio_bytes = await self.provider.generate_speech(args.text, args.voice)
        
        storage = get_storage_provider()
        artifact_id = storage.save_artifact(
            task_id=context.task_id or "default",
            data=audio_bytes,
            filename="tts_output.mp3",
            content_type="audio/mp3"
        )
        
        artifact_url = storage.get_artifact_url(artifact_id, context.task_id or "default")
        
        return ToolResult(
            tool_name=self.definition.id,
            status="success",
            output={
                "artifact_id": artifact_id,
                "artifact_url": artifact_url,
                "message": "Speech generated successfully."
            }
        )
