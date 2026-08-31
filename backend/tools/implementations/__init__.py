from tools.registry import registry as global_registry
from .mock import MockSuccessTool, MockErrorTool
from .web import WebSearchTool, BrowserOpenTool, WebScrapeTool
from .filesystem import FilesystemReadTool, FilesystemWriteTool
from .media import FFmpegTool, CloudinaryUploadTool
from .design import (
    CreativeDesignLayoutTool,
    CreativeMediaGenerateTool,
    CreativeMediaTransformTool,
    CreativeMediaAnimateTool,
)
from .animation import CreativeTechnicalAnimationTool
from .sourcing import CreativeStockSearchTool, CreativeSpeechGenerationTool
import logging

logger = logging.getLogger(__name__)

def register_all_tools(registry=global_registry):
    """
    Register all tools into the global Tool Registry.
    """
    tools = [
        MockSuccessTool(),
        MockErrorTool(),
        WebSearchTool(),
        BrowserOpenTool(),
        WebScrapeTool(),
        FilesystemReadTool(),
        FilesystemWriteTool(),
        FFmpegTool(),
        CloudinaryUploadTool(),
        CreativeDesignLayoutTool(),
        CreativeMediaGenerateTool(),
        CreativeMediaTransformTool(),
        CreativeMediaAnimateTool(),
        CreativeTechnicalAnimationTool(),
        CreativeStockSearchTool(),
        CreativeSpeechGenerationTool(),
    ]

    try:
        from teams.creative.common.tools.individual.ppt_generator import PPTGeneratorTool
        tools.append(PPTGeneratorTool())
    except ImportError as e:
        logger.warning(f"Could not load PPTGeneratorTool: {e}")

    try:
        from .website_generator import WebsiteGeneratorTool
        tools.append(WebsiteGeneratorTool())
    except ImportError as e:
        logger.warning(f"Could not load WebsiteGeneratorTool: {e}")

    for tool in tools:
        registry.register(tool)


register_all_tools()
