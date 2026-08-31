"""
Creative Agent
An agent specialized in visual design, brand identity, and AI-assisted media generation.
Produces images, videos, design assets, and social media content.
"""
import uuid
from datetime import datetime, timezone
import logging
from typing import Dict, Any, List, Optional

from agents.runtime.result import ToolRequest, ToolResult
from tools.gateway import CoreToolGateway

logger = logging.getLogger(__name__)


class CreativeAgent:
    """
    AI Agent for the Creative team.
    Produces:
    - Visual design assets (images, brand assets, social media content)
    - AI-generated images and video
    - Design layouts and brand materials
    - Motion graphics and animations
    """

    def __init__(self, employee_id: str = "emp_riya_sharma"):
        self.employee_id = employee_id
        self.session_id = str(uuid.uuid4())
        self.tool_gateway = CoreToolGateway()
        self.creative_skills = [
            "visual_design", "creative_direction", "storytelling",
            "composition", "branding", "typography", "color_theory",
            "ai_image_generation", "social_media_design", "storyboarding"
        ]
        self.creative_tools = [
            "creative.media.generate",
            "creative.media.transform",
            "creative.media.animate",
            "creative.design.layout",
            "ffmpeg",
            "cloudinary.upload",
        ]

    async def generate_asset(
        self,
        task_description: str,
        asset_type: str,
        context: str = "",
        style_guidance: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a creative asset (image, video, design layout, etc.).

        Args:
            task_description: What to create
            asset_type: One of image, video, design_layout, social_media, brand_asset
            context: Brand/project context
            style_guidance: Optional style or mood direction

        Returns:
            Dict with asset output, type, and session_id
        """
        valid_types = ["image", "video", "design_layout", "social_media", "brand_asset", "animation", "presentation"]
        if asset_type not in valid_types:
            return {
                "status": "error",
                "error": f"Invalid asset_type. Must be one of: {', '.join(valid_types)}",
                "session_id": self.session_id
            }

        tool_map = {
            "image":         "creative.media.generate",
            "video":         "creative.media.animate",
            "animation":     "creative.media.animate",
            "design_layout": "creative.design.layout",
            "social_media":  "creative.media.generate",
            "brand_asset":   "creative.design.layout",
            "presentation":  "creative.presentation.generate",
        }
        tool_name = tool_map[asset_type]

        logger.info(f"[CreativeAgent] generate_asset | type={asset_type} | task={task_description[:60]}")
        request = ToolRequest(
            tool_name=tool_name,
            employee_id="emp_cre_creator_001" if asset_type == "presentation" else self.employee_id,
            execution_id=self.session_id,
            arguments={
                "task_description": task_description,
                "asset_type": asset_type,
                "context": context,
                "style_guidance": style_guidance or "",
                "filename_prefix": "presentation" if asset_type == "presentation" else "asset",
            }
        )
        result = await self.tool_gateway.execute(request)
        if result.status == "success":
            return {
                "status": "success",
                "asset": result.output,
                "asset_type": asset_type,
                "session_id": self.session_id,
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
        logger.error(f"[CreativeAgent] Asset generation failed: {result.error}")
        return {"status": "error", "error": result.error, "session_id": self.session_id}

    async def review_design(
        self,
        asset_description: str,
        criteria: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Review a creative asset against design quality criteria.

        Args:
            asset_description: Description or URL of asset to review
            criteria: Specific criteria to check (composition, brand, typography, color)

        Returns:
            Dict with review feedback and recommendations
        """
        logger.info(f"[CreativeAgent] review_design | asset={asset_description[:60]}")
        request = ToolRequest(
            tool_name="creative.media.transform",
            employee_id=self.employee_id,
            execution_id=self.session_id,
            arguments={
                "asset_description": asset_description,
                "operation": "review",
                "criteria": criteria or ["composition", "brand_consistency", "typography", "color"],
            }
        )
        result = await self.tool_gateway.execute(request)
        if result.status == "success":
            return {
                "status": "success",
                "review": result.output,
                "session_id": self.session_id
            }
        return {"status": "error", "error": result.error, "session_id": self.session_id}

    async def refine_asset(
        self,
        original_asset: str,
        feedback: str,
        asset_type: str = "image"
    ) -> Dict[str, Any]:
        """Refine an existing asset based on feedback."""
        logger.info(f"[CreativeAgent] refine_asset | type={asset_type}")
        request = ToolRequest(
            tool_name="creative.media.transform",
            employee_id=self.employee_id,
            execution_id=self.session_id,
            arguments={
                "original_asset": original_asset,
                "feedback": feedback,
                "operation": "refine",
                "asset_type": asset_type,
            }
        )
        result = await self.tool_gateway.execute(request)
        if result.status == "success":
            return {
                "status": "success",
                "asset": result.output,
                "asset_type": asset_type,
                "session_id": self.session_id,
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
        return {"status": "error", "error": result.error, "session_id": self.session_id}
