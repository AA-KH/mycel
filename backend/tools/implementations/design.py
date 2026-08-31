"""
Creative Media Tools — Mycel Tool Implementations

Three generic creative media tools for Riya Sharma and the Creative Team.
These tools are the ONLY interface between the Reasoning Engine and the
MediaGenerationProvider layer. Riya never calls providers directly.

Tools:
    creative.media.generate  — Creates media from scratch (text → image/video)
    creative.media.transform — Transforms/varies existing media (image → image)
    creative.media.animate   — Animates still media into video (image → video)

Architecture:
    Riya (Agent)
        ↓
    creative.media.* (this file)
        ↓
    Security Gateway (CoreToolGateway enforces this)
        ↓
    MediaGenerationProvider selection
        ├── ComfyUIProvider  (primary: local GPU)
        └── PollinationsProvider  (fallback: free remote, images only)
        ↓
    ArtifactService → Cloudinary → ArtifactReference

Security:
    - Input artifact IDs are validated before use (no raw paths, no file://)
    - Source images are resolved through ArtifactService, not raw filesystem
    - All output goes through ArtifactService (no raw binary returned to LLM)

design.canvas (Penpot stub) is retained unchanged.
DesignCanvasTool, ImageGenerationTool, ImageVariationTool are REMOVED
and replaced by the three generic tools above.
"""

import json
import base64
import tempfile
import httpx
from typing import Any, Dict, Optional, List
import os
import tempfile

from tools.base import BaseTool
from tools.models import ToolDefinition
from agents.runtime.result import ToolResult
from tools.context import ToolExecutionContext
from core.logger import logger

from tools.providers.media import (
    MediaOperation,
    MediaGenerationRequest,
    CapabilityUnavailableError,
    MediaGenerationError,
)


# ─────────────────────────────────────────────────────────────────────────────
# Provider selection helpers
# ─────────────────────────────────────────────────────────────────────────────

def _get_comfyui_provider():
    from tools.providers.comfyui import ComfyUIProvider
    return ComfyUIProvider()


def _get_pollinations_provider():
    from tools.providers.pollinations import PollinationsProvider
    return PollinationsProvider()


def _get_cloudflare_provider():
    from tools.providers.cloudflare import CloudflareWorkerProvider
    return CloudflareWorkerProvider()


def _resolve_operation(operation_str: str) -> MediaOperation:
    """Convert string operation name to MediaOperation enum. Defaults to TEXT_TO_IMAGE."""
    try:
        return MediaOperation(operation_str.upper())
    except (ValueError, AttributeError):
        return MediaOperation.TEXT_TO_IMAGE


def _validate_no_raw_path(value: str, field: str):
    """
    Security: reject raw filesystem paths and file:// URIs as media inputs.
    Agents must pass ArtifactReference IDs, not filesystem paths.
    """
    if not value:
        return
    lowered = value.lower()
    forbidden = ["c:\\", "c:/", "/etc/", "/home/", "/root/", "file://", "../", "..\\"]
    for f in forbidden:
        if lowered.startswith(f) or f in lowered:
            raise ValueError(
                f"Security violation: raw filesystem path in '{field}' is not allowed. "
                f"Pass an ArtifactReference ID instead."
            )


async def _resolve_artifact_bytes(artifact_id: str, context: ToolExecutionContext) -> bytes:
    """
    Resolve an ArtifactReference ID to raw bytes for provider input.
    Downloads from Cloudinary URL or local storage as appropriate.
    """
    _validate_no_raw_path(artifact_id, "artifact_id")

    from artifacts import get_artifact_service
    service = get_artifact_service()

    artifact = await service.get_artifact(artifact_id)
    if not artifact:
        raise ValueError(f"ArtifactReference '{artifact_id}' not found.")

    url = artifact.secure_url or artifact.url
    if not url:
        raise ValueError(f"ArtifactReference '{artifact_id}' has no accessible URL.")

    async with httpx.AsyncClient(timeout=60) as client:
        res = await client.get(url)
        res.raise_for_status()
        return res.content


        logger.error(f"Failed to apply text overlays: {e}")
        return image_bytes


async def _save_as_artifact(
    media_bytes: bytes,
    artifact_type: str,  # "image" or "video"
    file_suffix: str,    # ".png" or ".mp4"
    context: ToolExecutionContext,
    parent_artifact_id: Optional[str] = None,
) -> ToolResult:
    """Save raw media bytes through the ArtifactService and return a ToolResult."""
    from artifacts import get_artifact_service

    service = get_artifact_service()
    fd, temp_path = tempfile.mkstemp(suffix=file_suffix)
    os.close(fd)

    try:
        with open(temp_path, "wb") as f:
            f.write(media_bytes)

        mime_type = "image/png" if artifact_type == "image" else "video/mp4"

        artifact_ref = await service.create_and_store(
            company_id=context.company_id,
            workspace_id=context.workspace_id or "default",
            task_id=context.task_id,
            execution_id=context.execution_id,
            employee_id=context.employee_id,
            artifact_type=artifact_type,
            file_path=temp_path,
            expected_output={"mime_type": mime_type},
            parent_artifact_id=parent_artifact_id,
        )

        return ToolResult(
            tool_name=f"creative.media.{artifact_type}",
            status="success",
            output={"artifact": artifact_ref.model_dump()},
            artifact_ids=[artifact_ref.artifact_id],
        )
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def _capability_unavailable_result(tool_name: str, error: CapabilityUnavailableError) -> ToolResult:
    """Return a structured, honest CAPABILITY_UNAVAILABLE result. Never fake success."""
    return ToolResult(
        tool_name=tool_name,
        status="capability_unavailable",
        output={
            "capability_error": str(error),
            "operation": error.operation,
            "provider": error.provider,
            "suggestion": (
                "This operation is not available on the current hardware/provider configuration. "
                "Consider an alternative operation (e.g. IMAGE_TO_VIDEO instead of TEXT_TO_VIDEO)."
            ),
        },
        error=None,  # Not an error — a declared capability boundary
    )


# ─────────────────────────────────────────────────────────────────────────────
# Tool 1: creative.media.generate
# Creates media from scratch (text → image, text → video)
# ─────────────────────────────────────────────────────────────────────────────

class CreativeMediaGenerateTool(BaseTool):
    """
    Generate creative media from a text prompt.

    Handles: TEXT_TO_IMAGE, TEXT_TO_VIDEO
    Primary provider: ComfyUIProvider (local GPU)
    Fallback provider: PollinationsProvider (images only, free remote)

    Riya uses this tool when no source asset exists and she is creating
    something entirely new from a description.
    """

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            id="creative.media.generate",
            name="Creative Media Generator",
            description=(
                "Generate an image or video from a text prompt. "
                "Use for: creating posters, banners, promotional images, "
                "and cinematic video scenes from scratch. "
                "Specify 'operation': 'TEXT_TO_IMAGE' (default) or 'TEXT_TO_VIDEO'."
            ),
            category="creative",
            enabled=True,
            requires_network=True,
            timeout_seconds=300,
            capabilities=["ai_image_generation", "creative_prompting", "visual_design", "GRAPHIC_DESIGN"],
            output_modalities=["IMAGE", "VIDEO"],
            artifact_types=["LOGO", "POSTER", "BANNER", "SOCIAL_MEDIA_CREATIVE", "ILLUSTRATION", "VIDEO"],
            preview_types=["IMAGE", "VIDEO_PLAYER"],
            input_schema={
                "type": "object",
                "required": ["prompt"],
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": (
                            "Detailed creative prompt. For promotional images, explicitly include "
                            'exact text in quotes (e.g. \'with text "Join Now!" in bold sans-serif\'), '
                            "layout description, color palette, and visual style. The FLUX model will render the text perfectly natively."
                        ),
                    },
                    "operation": {
                        "type": "string",
                        "enum": ["TEXT_TO_IMAGE", "TEXT_TO_VIDEO"],
                        "default": "TEXT_TO_IMAGE",
                        "description": "The media generation operation.",
                    },
                    "negative_prompt": {"type": "string"},
                    "width": {"type": "integer", "default": 512},
                    "height": {"type": "integer", "default": 512},
                    "duration_seconds": {
                        "type": "integer",
                        "default": 5,
                        "description": "Video duration in seconds (TEXT_TO_VIDEO only, max 8).",
                    },
                    "style": {"type": "string"},
                    "purpose": {"type": "string"},
                },
            },
        )

    async def execute(self, arguments: Dict[str, Any], context: ToolExecutionContext) -> ToolResult:
        from core.config import settings

        operation = _resolve_operation(arguments.get("operation", "TEXT_TO_IMAGE"))
        is_video = operation in (MediaOperation.TEXT_TO_VIDEO,)
        artifact_type = "video" if is_video else "image"
        file_suffix = ".mp4" if is_video else ".png"

        req = MediaGenerationRequest(
            operation=operation,
            prompt=arguments.get("prompt", ""),
            negative_prompt=arguments.get("negative_prompt"),
            width=int(arguments.get("width", 512)),
            height=int(arguments.get("height", 512)),
            duration_seconds=min(int(arguments.get("duration_seconds", 5)), 8),
            style=arguments.get("style"),
            purpose=arguments.get("purpose"),
        )

        # Primary for Images: Cloudflare Worker
        # Primary for Video: ComfyUI (Wan 2.1)
        if operation == MediaOperation.TEXT_TO_IMAGE:
            try:
                provider = _get_cloudflare_provider()
                logger.info("creative.media.generate [TEXT_TO_IMAGE] via CloudflareWorkerProvider (primary)")
                media_bytes = await provider.generate_image(req)
                return await _save_as_artifact(media_bytes, "image", ".png", context)
            except Exception as e:
                logger.warning(f"Cloudflare Worker failed: {e}. Falling back to Pollinations.")
                try:
                    provider = _get_pollinations_provider()
                    logger.info("creative.media.generate [TEXT_TO_IMAGE] via PollinationsProvider (fallback)")
                    media_bytes = await provider.generate_image(req)
                    return await _save_as_artifact(media_bytes, "image", ".png", context)
                except Exception as inner_e:
                    logger.error(f"Pollinations fallback failed: {inner_e}")
                    return ToolResult(
                        tool_name="creative.media.generate", 
                        status="error", 
                        error=f"Both primary (Cloudflare) and fallback (Pollinations) failed. Inner error: {inner_e}"
                    )
        elif operation == MediaOperation.TEXT_TO_VIDEO:
            try:
                provider = _get_comfyui_provider()
                logger.info(f"creative.media.generate [{operation}] via ComfyUIProvider (primary)")
                media_bytes = await provider.generate_video(req)
                return await _save_as_artifact(media_bytes, artifact_type, file_suffix, context)
            except CapabilityUnavailableError as e:
                return _capability_unavailable_result("creative.media.generate", e)
            except Exception as e:
                return ToolResult(tool_name="creative.media.generate", status="error", error=str(e))
        else:
            return ToolResult(tool_name="creative.media.generate", status="error", error=f"Unknown operation: {operation}")


# ─────────────────────────────────────────────────────────────────────────────
# Tool 2: creative.media.transform
# Transforms or varies an existing image
# ─────────────────────────────────────────────────────────────────────────────

class CreativeMediaTransformTool(BaseTool):
    """
    Transform or create variations of an existing image.

    Handles: IMAGE_TO_IMAGE (refine/improve), IMAGE_VARIATION (create N variants)
    Primary provider: ComfyUIProvider (local GPU, true img2img)
    Fallback provider: PollinationsProvider (txt2img approximation for VARIATION only)

    Original artifact is ALWAYS immutable. This tool always produces a NEW artifact.
    """

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            id="creative.media.transform",
            name="Creative Media Transformer",
            description=(
                "Transform or create variations of an existing image. "
                "Use for: improving an existing design (IMAGE_TO_IMAGE), "
                "or generating multiple variants of an image (IMAGE_VARIATION). "
                "The original image is always preserved — a new artifact is created."
            ),
            category="creative",
            enabled=True,
            requires_network=True,
            timeout_seconds=300,
            capabilities=["image_variation", "design_iteration", "creative_prompting"],
            input_schema={
                "type": "object",
                "required": ["prompt", "source_artifact_id"],
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "Describe how to transform or vary the source image.",
                    },
                    "source_artifact_id": {
                        "type": "string",
                        "description": "ArtifactReference ID of the source image. Do NOT use filesystem paths.",
                    },
                    "operation": {
                        "type": "string",
                        "enum": ["IMAGE_TO_IMAGE", "IMAGE_VARIATION"],
                        "default": "IMAGE_VARIATION",
                    },
                    "variation_strength": {
                        "type": "number",
                        "default": 0.7,
                        "description": "How much to change (0.0=minimal, 1.0=maximum). Default 0.7.",
                    },
                    "negative_prompt": {"type": "string"},
                },
            },
        )

    async def execute(self, arguments: Dict[str, Any], context: ToolExecutionContext) -> ToolResult:
        source_artifact_id = arguments.get("source_artifact_id", "")

        # Security: reject raw filesystem paths
        try:
            _validate_no_raw_path(source_artifact_id, "source_artifact_id")
        except ValueError as e:
            return ToolResult(
                tool_name="creative.media.transform",
                status="error",
                output={},
                error=str(e),
            )

        if not source_artifact_id:
            return ToolResult(
                tool_name="creative.media.transform",
                status="error",
                output={},
                error="source_artifact_id is required for creative.media.transform.",
            )

        operation = _resolve_operation(arguments.get("operation", "IMAGE_VARIATION"))

        # Resolve source image bytes from ArtifactReference
        try:
            source_bytes = await _resolve_artifact_bytes(source_artifact_id, context)
        except Exception as e:
            logger.error(f"creative.media.transform: could not resolve source artifact: {e}")
            return ToolResult(
                tool_name="creative.media.transform",
                status="error",
                output={},
                error=f"Could not resolve source artifact '{source_artifact_id}': {e}",
            )

        req = MediaGenerationRequest(
            operation=operation,
            prompt=arguments.get("prompt", ""),
            negative_prompt=arguments.get("negative_prompt"),
            source_image_bytes=source_bytes,
            source_image_artifact_id=source_artifact_id,
            variation_strength=float(arguments.get("variation_strength", 0.7)),
        )

        # Primary: ComfyUI
        try:
            provider = _get_comfyui_provider()
            logger.info(f"creative.media.transform [{operation}] via ComfyUIProvider")

            if operation == MediaOperation.IMAGE_TO_IMAGE:
                media_bytes = await provider.transform_image(req)
            else:
                media_bytes = await provider.create_variation(req)

            return await _save_as_artifact(
                media_bytes, "image", ".png", context,
                parent_artifact_id=source_artifact_id
            )

        except CapabilityUnavailableError as e:
            return _capability_unavailable_result("creative.media.transform", e)

        except Exception as e:
            logger.warning(f"creative.media.transform ComfyUI failed: {e}. Trying Pollinations fallback.")

        # Fallback: Pollinations (variation approximation via txt2img)
        if operation == MediaOperation.IMAGE_VARIATION:
            try:
                provider = _get_pollinations_provider()
                media_bytes = await provider.create_variation(req)
                return await _save_as_artifact(
                    media_bytes, "image", ".png", context,
                    parent_artifact_id=source_artifact_id
                )
            except Exception as inner_e:
                logger.error(f"creative.media.transform Pollinations fallback failed: {inner_e}")

        return ToolResult(
            tool_name="creative.media.transform",
            status="error",
            output={},
            error="All providers failed for creative.media.transform.",
        )


# ─────────────────────────────────────────────────────────────────────────────
# Tool 3: creative.media.animate
# Animates a still image into a video
# ─────────────────────────────────────────────────────────────────────────────

class CreativeMediaAnimateTool(BaseTool):
    """
    Animate a still image into a short video.

    Handles: IMAGE_TO_VIDEO, IMAGE_ANIMATION
    Primary provider: ComfyUIProvider → Wan 2.1 1.3B (8GB compatible)
    No fallback for video (Pollinations is images only).

    Examples:
        "Turn this poster into a 5 second animated reel"
        "Animate the background with floating particles"
        "Create a slow zoom-in camera movement on this product photo"
    """

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            id="creative.media.animate",
            name="Creative Media Animator",
            description=(
                "Animate a still image into a short video. "
                "Use for: turning posters into promotional reels (IMAGE_TO_VIDEO), "
                "creating subtle image animations (IMAGE_ANIMATION). "
                "Maximum 8 seconds. Requires Wan 2.1 1.3B model in ComfyUI."
            ),
            category="creative",
            enabled=True,
            requires_network=False,  # Uses local ComfyUI GPU
            timeout_seconds=480,     # Video generation is slower than images
            capabilities=["image_animation", "creative_video_direction", "visual_storytelling"],
            input_schema={
                "type": "object",
                "required": ["prompt", "source_artifact_id"],
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "Describe the visual content and animation result.",
                    },
                    "source_artifact_id": {
                        "type": "string",
                        "description": "ArtifactReference ID of the source image. Do NOT use filesystem paths.",
                    },
                    "operation": {
                        "type": "string",
                        "enum": ["IMAGE_TO_VIDEO", "IMAGE_ANIMATION"],
                        "default": "IMAGE_TO_VIDEO",
                    },
                    "motion_prompt": {
                        "type": "string",
                        "description": (
                            "Describes the motion/animation style. "
                            "Examples: 'slow zoom in', 'particles floating upward', "
                            "'camera pan left, subtle glow pulses'."
                        ),
                    },
                    "duration_seconds": {
                        "type": "integer",
                        "default": 5,
                        "description": "Video duration 1–8 seconds.",
                    },
                    "fps": {
                        "type": "integer",
                        "default": 16,
                        "description": "Frames per second.",
                    },
                    "negative_prompt": {"type": "string"},
                    "aspect_ratio": {"type": "string"},
                },
            },
        )

    async def execute(self, arguments: Dict[str, Any], context: ToolExecutionContext) -> ToolResult:
        source_artifact_id = arguments.get("source_artifact_id", "")

        # Security: no raw paths
        try:
            _validate_no_raw_path(source_artifact_id, "source_artifact_id")
        except ValueError as e:
            return ToolResult(
                tool_name="creative.media.animate",
                status="error",
                output={},
                error=str(e),
            )

        if not source_artifact_id:
            return ToolResult(
                tool_name="creative.media.animate",
                status="error",
                output={},
                error="source_artifact_id is required for creative.media.animate.",
            )

        operation = _resolve_operation(arguments.get("operation", "IMAGE_TO_VIDEO"))

        # Resolve source bytes
        try:
            source_bytes = await _resolve_artifact_bytes(source_artifact_id, context)
        except Exception as e:
            logger.error(f"creative.media.animate: could not resolve source artifact: {e}")
            return ToolResult(
                tool_name="creative.media.animate",
                status="error",
                output={},
                error=f"Could not resolve source artifact '{source_artifact_id}': {e}",
            )

        req = MediaGenerationRequest(
            operation=operation,
            prompt=arguments.get("prompt", ""),
            negative_prompt=arguments.get("negative_prompt"),
            source_image_bytes=source_bytes,
            source_image_artifact_id=source_artifact_id,
            motion_prompt=arguments.get("motion_prompt"),
            duration_seconds=min(int(arguments.get("duration_seconds", 5)), 8),
            fps=int(arguments.get("fps", 16)),
            aspect_ratio=arguments.get("aspect_ratio"),
        )

        try:
            provider = _get_comfyui_provider()
            logger.info(
                f"creative.media.animate [{operation}] via ComfyUIProvider "
                f"(duration={req.duration_seconds}s, fps={req.fps})"
            )
            media_bytes = await provider.animate_image(req)
            return await _save_as_artifact(
                media_bytes, "video", ".mp4", context,
                parent_artifact_id=source_artifact_id
            )

        except CapabilityUnavailableError as e:
            return _capability_unavailable_result("creative.media.animate", e)

        except Exception as e:
            logger.error(f"creative.media.animate failed: {e}")
            return ToolResult(
                tool_name="creative.media.animate",
                status="error",
                output={},
                error=f"Animation generation failed: {e}",
            )


# ─────────────────────────────────────────────────────────────────────────────
# creative.design.layout
# Renders HTML/CSS layout (with optional background) to a final image
# ─────────────────────────────────────────────────────────────────────────────

class CreativeDesignLayoutTool(BaseTool):
    """
    Renders an HTML/CSS layout into a final structured image using Playwright.
    Allows exact typography, margins, and graphics placement over backgrounds.
    """

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            id="creative.design.layout",
            name="Creative Design Layout Engine",
            description=(
                "Renders an HTML/CSS layout into a final polished image. "
                "Use this to structure precise typography, margins, logos, and elements "
                "over a previously generated background image. "
                "You must provide valid HTML and CSS. Background image is injected automatically."
            ),
            category="creative",
            enabled=True,
            timeout_seconds=60,
            input_schema={
                "type": "object",
                "properties": {
                    "html": {"type": "string", "description": "The HTML content inside the body tag."},
                    "css": {"type": "string", "description": "CSS styles (do not include <style> tags)."},
                    "background_artifact_id": {
                        "type": "string", 
                        "description": "ArtifactReference ID of the background image."
                    },
                    "width": {"type": "integer", "default": 1024},
                    "height": {"type": "integer", "default": 1024},
                },
                "required": ["html", "css", "background_artifact_id"],
            },
        )

    async def execute(self, arguments: Dict[str, Any], context: ToolExecutionContext) -> ToolResult:
        html_content = arguments.get("html", "")
        css_content = arguments.get("css", "")
        bg_artifact_id = arguments.get("background_artifact_id", "")
        width = int(arguments.get("width", 1024))
        height = int(arguments.get("height", 1024))

        try:
            _validate_no_raw_path(bg_artifact_id, "background_artifact_id")
        except ValueError as e:
            return ToolResult(tool_name="creative.design.layout", status="error", error=str(e))

        # Fetch background image base64
        import base64
        try:
            bg_bytes = await _resolve_artifact_bytes(bg_artifact_id, context)
            bg_b64 = base64.b64encode(bg_bytes).decode("utf-8")
            bg_data_uri = f"data:image/png;base64,{bg_b64}"
        except Exception as e:
            logger.error(f"Failed to fetch background: {e}")
            return ToolResult(tool_name="creative.design.layout", status="error", error=f"Background fetch failed: {e}")

        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&family=Playfair+Display:wght@700&family=Montserrat:wght@800&display=swap');
                
                body {{
                    margin: 0;
                    padding: 0;
                    width: {width}px;
                    height: {height}px;
                    background-image: url('{bg_data_uri}');
                    background-size: cover;
                    background-position: center;
                    overflow: hidden;
                    position: relative;
                }}
                
                {css_content}
            </style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """

        try:
            from playwright.async_api import async_playwright
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page(viewport={"width": width, "height": height})
                await page.set_content(full_html, wait_until="networkidle")
                
                # Take screenshot
                screenshot_bytes = await page.screenshot(type="png", full_page=True)
                await browser.close()
                
            return await _save_as_artifact(
                screenshot_bytes, "image", ".png", context,
                parent_artifact_id=bg_artifact_id
            )
            
        except ImportError:
            return ToolResult(
                tool_name="creative.design.layout", 
                status="error", 
                error="playwright is not installed. Run: pip install playwright && playwright install chromium"
            )
        except Exception as e:
            logger.error(f"Playwright rendering failed: {e}")
            return ToolResult(tool_name="creative.design.layout", status="error", output={}, error=str(e))

