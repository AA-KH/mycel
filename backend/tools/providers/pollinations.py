"""
Pollinations Provider — Mycel Creative Media System

Free, no-API-key image generation using Pollinations.ai (FLUX model).
Implements MediaGenerationProvider for the image subset only.

Supported operations:
    TEXT_TO_IMAGE   — FLUX via Pollinations.ai endpoint
    IMAGE_VARIATION — Uses variation prompt as a new txt2img (Pollinations is txt2img only)

NOT supported (raises CapabilityUnavailableError):
    IMAGE_TO_IMAGE      — Pollinations has no img2img endpoint
    TEXT_TO_VIDEO       — Pollinations has no video endpoint
    IMAGE_TO_VIDEO      — Pollinations has no video endpoint
    IMAGE_ANIMATION     — Pollinations has no video endpoint
    MULTI_IMAGE_TO_VIDEO — Pollinations has no video endpoint

This provider is used as a fallback when ComfyUI is unavailable (offline, OOM, etc.).
It is always free, requires no credentials, and uses the FLUX model by default.

Rate limiting: Pollinations enforces per-URL limits. We inject a random seed
on every request to ensure unique URLs and avoid 429 collisions.
"""

import random
import urllib.parse
from typing import List

import httpx

from core.logger import logger
from .media import (
    MediaGenerationProvider,
    MediaGenerationRequest,
    MediaOperation,
    CapabilityUnavailableError,
)

_SUPPORTED_OPERATIONS = [
    MediaOperation.TEXT_TO_IMAGE,
    MediaOperation.IMAGE_VARIATION,
]


class PollinationsProvider(MediaGenerationProvider):
    """
    Free remote image provider using Pollinations.ai FLUX.
    No API keys required. Used as the fallback when ComfyUI is unavailable.

    Limitations:
        - Text-to-image only (no img2img, no video)
        - Subject to public rate limits (~1 req/2s)
        - IMAGE_VARIATION is approximated via a descriptive txt2img prompt
          (Pollinations has no true img2img endpoint)
    """

    BASE_URL = "https://image.pollinations.ai/prompt"
    TIMEOUT = 90  # seconds — FLUX can be slow on busy servers

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "MycelCreativeAgent/1.0"
        )
    }

    def supported_operations(self) -> List[MediaOperation]:
        return _SUPPORTED_OPERATIONS

    def _build_url(self, prompt: str, width: int, height: int, seed: int) -> str:
        safe_prompt = urllib.parse.quote(prompt)
        return (
            f"{self.BASE_URL}/{safe_prompt}"
            f"?width={width}&height={height}"
            f"&nologo=True&model=flux"
            f"&seed={seed}"
        )

    async def generate_image(self, request: MediaGenerationRequest) -> bytes:
        """TEXT_TO_IMAGE using FLUX via Pollinations.ai."""
        seed = request.seed or random.randint(1, 1_000_000)
        url = self._build_url(request.prompt, request.width, request.height, seed)
        logger.info(f"Pollinations generating image: {request.prompt[:60]}...")

        async with httpx.AsyncClient(timeout=self.TIMEOUT, headers=self.HEADERS) as client:
            res = await client.get(url)
            res.raise_for_status()
            logger.info(f"Pollinations image received ({len(res.content)} bytes).")
            return res.content

    async def generate_video(self, request: MediaGenerationRequest) -> bytes:
        raise CapabilityUnavailableError(
            operation=MediaOperation.TEXT_TO_VIDEO,
            provider="PollinationsProvider",
            reason="Pollinations.ai does not support video generation.",
        )

    async def transform_image(self, request: MediaGenerationRequest) -> bytes:
        raise CapabilityUnavailableError(
            operation=MediaOperation.IMAGE_TO_IMAGE,
            provider="PollinationsProvider",
            reason=(
                "Pollinations.ai is a text-to-image service and does not support "
                "image-to-image transformation. Use ComfyUIProvider for img2img operations."
            ),
        )

    async def create_variation(self, request: MediaGenerationRequest) -> bytes:
        """
        IMAGE_VARIATION approximated via txt2img.
        Pollinations has no true img2img, so we use the prompt describing the variation.
        A new random seed ensures a fresh image every time.
        """
        seed = (request.seed + 1) if request.seed else random.randint(1, 1_000_000)
        url = self._build_url(request.prompt, request.width, request.height, seed)
        logger.info(f"Pollinations generating variation (txt2img approximation): {request.prompt[:60]}...")

        async with httpx.AsyncClient(timeout=self.TIMEOUT, headers=self.HEADERS) as client:
            res = await client.get(url)
            res.raise_for_status()
            logger.info(f"Pollinations variation received ({len(res.content)} bytes).")
            return res.content

    async def animate_image(self, request: MediaGenerationRequest) -> bytes:
        raise CapabilityUnavailableError(
            operation=MediaOperation.IMAGE_TO_VIDEO,
            provider="PollinationsProvider",
            reason="Pollinations.ai does not support video or image animation.",
        )
