from enum import Enum
from typing import Dict, List

class MediaOperation(str, Enum):
    TEXT_TO_VIDEO = "TEXT_TO_VIDEO"
    IMAGE_TO_VIDEO = "IMAGE_TO_VIDEO"
    MULTI_IMAGE_TO_VIDEO = "MULTI_IMAGE_TO_VIDEO"
    VIDEO_TO_VIDEO = "VIDEO_TO_VIDEO"
    IMAGE_TO_IMAGE = "IMAGE_TO_IMAGE"
    IMAGE_VARIATION = "IMAGE_VARIATION"
    VIDEO_EDITING = "VIDEO_EDITING"
    VIDEO_COMPOSITION = "VIDEO_COMPOSITION"
    TECHNICAL_ANIMATION = "TECHNICAL_ANIMATION"
    STOCK_VIDEO_COMPOSITION = "STOCK_VIDEO_COMPOSITION"
    AVATAR_VIDEO = "AVATAR_VIDEO"
    VOICEOVER_VIDEO = "VOICEOVER_VIDEO"

class CreativeIntent(str, Enum):
    TECHNICAL_EXPLAINER = "technical_explainer"
    SOCIAL_MEDIA_ANIMATION = "social_media_animation"
    PRODUCT_AD_VIDEO = "product_ad_video"
    STOCK_MEDIA_VIDEO = "stock_media_video"
    COMMERCIAL_VIDEO = "commercial_video"

def resolve_operation_from_intent(intent: str) -> MediaOperation:
    """
    Resolve the high-level user intent to a specific MediaOperation.
    """
    mapping: Dict[str, MediaOperation] = {
        CreativeIntent.TECHNICAL_EXPLAINER: MediaOperation.TECHNICAL_ANIMATION,
        CreativeIntent.SOCIAL_MEDIA_ANIMATION: MediaOperation.IMAGE_TO_VIDEO,
        CreativeIntent.PRODUCT_AD_VIDEO: MediaOperation.MULTI_IMAGE_TO_VIDEO,
        CreativeIntent.STOCK_MEDIA_VIDEO: MediaOperation.STOCK_VIDEO_COMPOSITION,
        CreativeIntent.COMMERCIAL_VIDEO: MediaOperation.VIDEO_COMPOSITION,
    }
    return mapping.get(intent, MediaOperation.TEXT_TO_VIDEO)

def get_required_capabilities(operation: MediaOperation) -> List[str]:
    """
    Map MediaOperation to required creative capabilities.
    """
    mapping: Dict[MediaOperation, List[str]] = {
        MediaOperation.TECHNICAL_ANIMATION: ["technical_animation", "storytelling", "algorithm_visualization"],
        MediaOperation.IMAGE_TO_VIDEO: ["motion_design", "video_generation", "video_post_processing"],
        MediaOperation.MULTI_IMAGE_TO_VIDEO: ["video_composition", "storytelling", "motion_design"],
        MediaOperation.STOCK_VIDEO_COMPOSITION: ["stock_media_sourcing", "video_composition", "motion_design"],
        MediaOperation.VIDEO_COMPOSITION: ["creative_direction", "storyboarding", "visual_storytelling", "video_generation", "video_composition"],
    }
    return mapping.get(operation, ["video_generation"])
