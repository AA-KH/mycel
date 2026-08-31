"""
Media Generation Domain Models — Mycel Creative Media System

This module defines the canonical contracts for all creative media generation
in Mycel. Providers, tools, and the reasoning engine all speak this language.

Architecture:
    Riya (Agent)
        ↓
    TaskIntent (media_operation resolved)
        ↓
    creative.media.* Tool
        ↓
    MediaGenerationProvider (this interface)
        ↓
    ComfyUIProvider / PollinationsProvider
        ↓
    ArtifactService → Cloudinary → ArtifactReference

IMPORTANT: Riya must never know which provider executed her request.
           She should only know WHAT she asked for and WHAT she received.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# ─────────────────────────────────────────────────────────────────────────────
# Media Operations
# ─────────────────────────────────────────────────────────────────────────────

class MediaOperation(str, Enum):
    """
    The set of creative media operations supported by the Mycel platform.

    Only register operations that are actually implemented by at least one provider.
    Providers declare which subset they support via supported_operations().
    """
    TEXT_TO_IMAGE       = "TEXT_TO_IMAGE"       # Prompt → image
    IMAGE_TO_IMAGE      = "IMAGE_TO_IMAGE"       # Image + prompt → refined image
    IMAGE_VARIATION     = "IMAGE_VARIATION"      # Image → N variant images (original immutable)
    TEXT_TO_VIDEO       = "TEXT_TO_VIDEO"        # Prompt → video
    IMAGE_TO_VIDEO      = "IMAGE_TO_VIDEO"       # Image + motion prompt → video
    MULTI_IMAGE_TO_VIDEO = "MULTI_IMAGE_TO_VIDEO" # N images → video (slideshow/transition)
    IMAGE_ANIMATION     = "IMAGE_ANIMATION"      # Image → animated video (e.g. subtle motion)


# ─────────────────────────────────────────────────────────────────────────────
# Normalized Request
# ─────────────────────────────────────────────────────────────────────────────

class MediaGenerationRequest(BaseModel):
    """
    Normalized, provider-agnostic request for any creative media operation.

    The tool layer constructs this from the agent's tool arguments and the
    resolved TaskIntent. The provider receives this and decides HOW to execute
    it internally (model selection, workflow construction, etc.).

    Agents and tools should NEVER pass ComfyUI workflow IDs, model names,
    checkpoint filenames, or node IDs. Those are provider-internal concerns.
    """

    # Core operation
    operation: MediaOperation = Field(
        ...,
        description="The media operation to perform. Determines which provider method is invoked."
    )
    prompt: str = Field(
        ...,
        description="Primary creative prompt describing the desired output."
    )
    negative_prompt: Optional[str] = Field(
        None,
        description="What to avoid in the generated output."
    )

    # Source inputs (for transform/animate operations)
    source_image_bytes: Optional[bytes] = Field(
        None,
        description=(
            "Raw bytes of the source image for IMAGE_TO_IMAGE, IMAGE_VARIATION, "
            "IMAGE_TO_VIDEO, and IMAGE_ANIMATION operations. "
            "Never populated from raw filesystem paths — always resolved from ArtifactReference."
        )
    )
    source_image_artifact_id: Optional[str] = Field(
        None,
        description="ArtifactReference ID of the source image. Used for audit and lineage."
    )
    additional_source_image_bytes: Optional[List[bytes]] = Field(
        None,
        description="Additional source images for MULTI_IMAGE_TO_VIDEO."
    )

    # Image output dimensions (bounded by provider for 8GB VRAM safety)
    width: int = Field(512, description="Target width in pixels. Provider may clamp for VRAM safety.")
    height: int = Field(512, description="Target height in pixels. Provider may clamp for VRAM safety.")

    # Video-specific parameters
    duration_seconds: int = Field(
        5,
        ge=1,
        le=8,
        description=(
            "Requested video duration in seconds. "
            "Bounded to 8s max for 8GB VRAM. Provider may further restrict."
        )
    )
    fps: int = Field(16, description="Frames per second. Lightweight default for local GPU.")
    motion_prompt: Optional[str] = Field(
        None,
        description="Text describing the desired motion/animation (for IMAGE_TO_VIDEO)."
    )

    # Post-generation text overlays
    text_overlays: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Text to be rendered perfectly over the image via post-processing."
    )

    # Optional styling metadata
    style: Optional[str] = Field(None, description="E.g. 'cinematic', 'flat design'")
    purpose: Optional[str] = Field(None, description="E.g. 'social_media', 'promotional'")

    # Sampling parameters (provider may override for resource safety)
    steps: int = Field(25, description="Diffusion steps.")
    guidance_scale: float = Field(7.0, description="CFG scale.")
    seed: Optional[int] = Field(None, description="Random seed for reproducibility.")
    aspect_ratio: Optional[str] = Field(
        None,
        description="Target aspect ratio, e.g. '16:9', '9:16', '1:1'."
    )
    variation_strength: float = Field(
        0.7,
        description="Denoising strength for IMAGE_TO_IMAGE / IMAGE_VARIATION (0.0–1.0)."
    )


# ─────────────────────────────────────────────────────────────────────────────
# Errors
# ─────────────────────────────────────────────────────────────────────────────

class CapabilityUnavailableError(Exception):
    """
    Raised by a MediaGenerationProvider when the requested operation is not
    supported by this provider (e.g. TEXT_TO_VIDEO on an 8GB GPU without a
    T2V model checkpoint installed).

    This is NOT an execution failure. It is a capability boundary signal.

    The tool layer catches this and returns a structured
    status="capability_unavailable" ToolResult — never a fake success.
    """
    def __init__(self, operation: MediaOperation, provider: str, reason: str):
        self.operation = operation
        self.provider = provider
        self.reason = reason
        super().__init__(
            f"[{provider}] Operation '{operation}' is not available: {reason}"
        )


class MediaGenerationError(Exception):
    """
    Raised when a provider attempts an operation but encounters an execution
    failure (network error, model OOM, timeout, invalid workflow, etc.).

    Distinct from CapabilityUnavailableError: the operation is supported but
    the specific execution failed.
    """
    def __init__(self, operation: MediaOperation, provider: str, reason: str):
        self.operation = operation
        self.provider = provider
        self.reason = reason
        super().__init__(f"[{provider}] Generation failed for '{operation}': {reason}")


# ─────────────────────────────────────────────────────────────────────────────
# Provider Interface
# ─────────────────────────────────────────────────────────────────────────────

class MediaGenerationProvider(ABC):
    """
    Abstract interface for all creative media generation providers in Mycel.

    Providers implement ONLY the operations they support.
    Unsupported operations MUST raise CapabilityUnavailableError — never fake results.

    Capability declaration via supported_operations() allows the tool layer
    to select the correct provider or fail gracefully without guessing.

    Concrete implementations:
        - ComfyUIProvider  — local GPU, primary (image + image-to-video via Wan 2.1)
        - PollinationsProvider — free remote fallback (images only)
    """

    @abstractmethod
    def supported_operations(self) -> List[MediaOperation]:
        """
        Declares which MediaOperations this provider can execute.
        The tool layer uses this to select providers and handle unsupported cases.
        """
        pass

    def supports(self, operation: MediaOperation) -> bool:
        """Convenience check."""
        return operation in self.supported_operations()

    @abstractmethod
    async def generate_image(self, request: MediaGenerationRequest) -> bytes:
        """
        TEXT_TO_IMAGE: Generate an image from a text prompt.
        Returns raw image bytes (PNG).
        Raises CapabilityUnavailableError if not supported.
        Raises MediaGenerationError on execution failure.
        """
        pass

    @abstractmethod
    async def generate_video(self, request: MediaGenerationRequest) -> bytes:
        """
        TEXT_TO_VIDEO: Generate a video from a text prompt.
        Returns raw video bytes (MP4).
        Raises CapabilityUnavailableError if not supported.
        Raises MediaGenerationError on execution failure.
        """
        pass

    @abstractmethod
    async def transform_image(self, request: MediaGenerationRequest) -> bytes:
        """
        IMAGE_TO_IMAGE: Transform / refine an existing image with a new prompt.
        Requires request.source_image_bytes.
        Returns raw image bytes (PNG).
        Raises CapabilityUnavailableError if not supported.
        """
        pass

    @abstractmethod
    async def create_variation(self, request: MediaGenerationRequest) -> bytes:
        """
        IMAGE_VARIATION: Generate a variation of an existing image.
        Original artifact must remain immutable — this always produces a NEW artifact.
        Requires request.source_image_bytes.
        Returns raw image bytes (PNG).
        Raises CapabilityUnavailableError if not supported.
        """
        pass

    @abstractmethod
    async def animate_image(self, request: MediaGenerationRequest) -> bytes:
        """
        IMAGE_TO_VIDEO / IMAGE_ANIMATION: Animate a still image into a short video.
        Requires request.source_image_bytes.
        Uses request.motion_prompt, duration_seconds, fps.
        Returns raw video bytes (MP4).
        Raises CapabilityUnavailableError if not supported.
        Raises MediaGenerationError on execution failure.
        """
        pass
