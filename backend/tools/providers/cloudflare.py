"""
Cloudflare Worker Provider — Mycel Creative Media System

Custom provider integrating with a Cloudflare Worker for image generation.
This uses a POST request with JSON payload containing the prompt.
"""

from typing import List

import httpx

from core.config import settings
from core.logger import logger
from .media import (
    MediaGenerationProvider,
    MediaGenerationRequest,
    MediaOperation,
    CapabilityUnavailableError,
)

_SUPPORTED_OPERATIONS = [
    MediaOperation.TEXT_TO_IMAGE,
]


class CloudflareWorkerProvider(MediaGenerationProvider):
    """
    Image provider using a custom Cloudflare Worker endpoint.
    """

    def __init__(self):
        self.url = settings.cloudflare_image_worker_url.rstrip("/")
        self.api_key = settings.cloudflare_image_worker_key
        self.timeout = 120

    def supported_operations(self) -> List[MediaOperation]:
        return _SUPPORTED_OPERATIONS

    async def generate_image(self, request: MediaGenerationRequest) -> bytes:
        """TEXT_TO_IMAGE via Cloudflare Worker."""
        logger.info(f"Cloudflare Worker generating image: {request.prompt[:60]}...")

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "MycelCreativeAgent/1.0"
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "prompt": request.prompt
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                res = await client.post(self.url, headers=headers, json=payload)
                res.raise_for_status()
                logger.info(f"Cloudflare Worker image received ({len(res.content)} bytes).")
                return res.content
            except httpx.HTTPStatusError as e:
                logger.error(f"Cloudflare Worker HTTP error: {e.response.status_code} - {e.response.text}")
                raise

    async def generate_video(self, request: MediaGenerationRequest) -> bytes:
        raise CapabilityUnavailableError(
            operation=MediaOperation.TEXT_TO_VIDEO,
            provider="CloudflareWorkerProvider",
            reason="Cloudflare Worker does not support video generation.",
        )

    async def transform_image(self, request: MediaGenerationRequest) -> bytes:
        raise CapabilityUnavailableError(
            operation=MediaOperation.IMAGE_TO_IMAGE,
            provider="CloudflareWorkerProvider",
            reason="Cloudflare Worker does not support image-to-image transformation.",
        )

    async def create_variation(self, request: MediaGenerationRequest) -> bytes:
        raise CapabilityUnavailableError(
            operation=MediaOperation.IMAGE_VARIATION,
            provider="CloudflareWorkerProvider",
            reason="Cloudflare Worker does not support image variation.",
        )

    async def animate_image(self, request: MediaGenerationRequest) -> bytes:
        raise CapabilityUnavailableError(
            operation=MediaOperation.IMAGE_TO_VIDEO,
            provider="CloudflareWorkerProvider",
            reason="Cloudflare Worker does not support video or image animation.",
        )
