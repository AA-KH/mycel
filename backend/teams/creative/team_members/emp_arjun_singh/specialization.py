from ...common.capabilities import CreativeIntent, MediaOperation

class ArjunSpecialization:
    """
    Arjun's specialized mappings for intent to media operations.
    """
    
    @staticmethod
    def resolve_intent(intent: str) -> MediaOperation:
        # Arjun handles specific intents differently or supports specific ones
        mapping = {
            CreativeIntent.TECHNICAL_EXPLAINER: MediaOperation.TECHNICAL_ANIMATION,
            CreativeIntent.SOCIAL_MEDIA_ANIMATION: MediaOperation.IMAGE_TO_VIDEO,
            CreativeIntent.PRODUCT_AD_VIDEO: MediaOperation.MULTI_IMAGE_TO_VIDEO,
            CreativeIntent.STOCK_MEDIA_VIDEO: MediaOperation.STOCK_VIDEO_COMPOSITION,
            CreativeIntent.COMMERCIAL_VIDEO: MediaOperation.VIDEO_COMPOSITION,
        }
        return mapping.get(intent, MediaOperation.TEXT_TO_VIDEO)
