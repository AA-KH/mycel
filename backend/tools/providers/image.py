"""
Backwards-compatible image provider interface — Mycel

ImageGenerationRequest and ImageGenerationProvider are retained as aliases
so that existing tests and imports do not break. New code should use the
canonical types from tools.providers.media instead.
"""

# Re-export canonical types under legacy names for backwards compatibility
from .media import (
    MediaGenerationRequest as ImageGenerationRequest,
    MediaGenerationProvider as ImageGenerationProvider,
)

__all__ = ["ImageGenerationRequest", "ImageGenerationProvider"]

