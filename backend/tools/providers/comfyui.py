"""
ComfyUI Provider — Mycel Creative Media System

Implements MediaGenerationProvider using the ComfyUI HTTP API as the execution
backend. ComfyUI runs as a SEPARATE process — it is NOT embedded into Mycel.

Riya does not know ComfyUI exists. She requests a MediaOperation and receives
an ArtifactReference. The routing Riya → Tool → Provider → ComfyUI is invisible.

Supported operations (8GB VRAM, batch_size=1):
    TEXT_TO_IMAGE       — SD 1.5 txt2img workflow
    IMAGE_TO_IMAGE      — SD 1.5 img2img workflow (VAEEncode + KSampler)
    IMAGE_VARIATION     — Same as img2img with variation_strength
    IMAGE_TO_VIDEO      — Wan 2.1 1.3B i2v workflow (explicitly ~8GB compatible)
    IMAGE_ANIMATION     — Same as IMAGE_TO_VIDEO with sensible motion defaults

NOT supported (raises CapabilityUnavailableError):
    TEXT_TO_VIDEO       — No T2V checkpoint assumed on 8GB development machine
    MULTI_IMAGE_TO_VIDEO — Not implemented in this phase

Config (all via .env / Settings):
    COMFYUI_BASE_URL          — default http://127.0.0.1:8188
    COMFYUI_API_KEY           — optional Bearer token
    COMFYUI_TIMEOUT_SECONDS   — default 120
    COMFYUI_MAX_RETRIES       — default 2
    COMFYUI_WAN_MODEL         — Wan 2.1 1.3B checkpoint filename
    COMFYUI_VIDEO_DEFAULT_FPS — default 16
"""

import json
import asyncio
import random
from typing import Dict, Any, List, Optional

import httpx

from core.config import settings
from core.logger import logger
from .media import (
    MediaGenerationProvider,
    MediaGenerationRequest,
    MediaOperation,
    CapabilityUnavailableError,
    MediaGenerationError,
)


# Operations this provider can execute on a local 8GB GPU
_SUPPORTED_OPERATIONS = [
    MediaOperation.TEXT_TO_IMAGE,
    MediaOperation.IMAGE_TO_IMAGE,
    MediaOperation.IMAGE_VARIATION,
    MediaOperation.IMAGE_TO_VIDEO,
    MediaOperation.IMAGE_ANIMATION,
]


class ComfyUIProvider(MediaGenerationProvider):
    """
    Local ComfyUI integration — primary creative media provider for Mycel.

    All workflow JSON is constructed natively in Python. No ComfyUI source
    code is copied. No ComfyUI repository is vendored. Mycel communicates
    exclusively via the ComfyUI HTTP API.

    8GB VRAM guardrails:
        - Images: max 1024×1024, batch_size=1
        - Video:  max 480p, duration ≤ 8s, fps ≤ 24, batch_size=1
        - Models: SD 1.5 (image), Wan 2.1 1.3B (video)
    """

    def __init__(self):
        self.base_url = getattr(settings, "comfyui_base_url", "http://127.0.0.1:8188").rstrip("/")
        self.timeout = int(getattr(settings, "comfyui_timeout_seconds", 180))
        self.max_retries = int(getattr(settings, "comfyui_max_retries", 2))
        self.api_key: Optional[str] = getattr(settings, "comfyui_api_key", None)

        # Image VRAM caps
        self.max_image_width = 1024
        self.max_image_height = 1024

        # Video VRAM caps (Wan 2.1 1.3B 480P)
        self.max_video_width = 832
        self.max_video_height = 480
        self.max_video_duration = int(getattr(settings, "comfyui_video_max_duration", 8))
        self.default_video_fps = int(getattr(settings, "comfyui_video_default_fps", 16))

        # Wan 2.1 1.3B checkpoint — user must install this in ComfyUI models/
        self.wan_model: str = getattr(
            settings, "comfyui_wan_model", "wan2.1-i2v-1.3B-480P.safetensors"
        )

    # ──────────────────────────────────────────────────────────────────────────
    # Capability declaration
    # ──────────────────────────────────────────────────────────────────────────

    def supported_operations(self) -> List[MediaOperation]:
        return _SUPPORTED_OPERATIONS

    # ──────────────────────────────────────────────────────────────────────────
    # Workflow builders
    # ──────────────────────────────────────────────────────────────────────────

    def _build_txt2img_workflow(self, request: MediaGenerationRequest) -> Dict[str, Any]:
        """SD 1.5 txt2img — lightweight, 8GB compatible."""
        width = min(request.width, self.max_image_width)
        height = min(request.height, self.max_image_height)
        seed = request.seed or random.randint(1, 2**31)

        return {
            "3": {
                "class_type": "KSampler",
                "inputs": {
                    "seed": seed,
                    "steps": request.steps,
                    "cfg": request.guidance_scale,
                    "sampler_name": "euler",
                    "scheduler": "normal",
                    "denoise": 1.0,
                    "model": ["4", 0],
                    "positive": ["6", 0],
                    "negative": ["7", 0],
                    "latent_image": ["5", 0],
                },
            },
            "4": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {"ckpt_name": "v1-5-pruned-emaonly.safetensors"},
            },
            "5": {
                "class_type": "EmptyLatentImage",
                "inputs": {"batch_size": 1, "width": width, "height": height},
            },
            "6": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": request.prompt, "clip": ["4", 1]},
            },
            "7": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "text": request.negative_prompt or "text, watermark, ugly, low quality, blurry",
                    "clip": ["4", 1],
                },
            },
            "8": {
                "class_type": "VAEDecode",
                "inputs": {"samples": ["3", 0], "vae": ["4", 2]},
            },
            "9": {
                "class_type": "SaveImage",
                "inputs": {"filename_prefix": "mycel_img", "images": ["8", 0]},
            },
        }

    def _build_img2img_workflow(
        self, request: MediaGenerationRequest, source_filename: str
    ) -> Dict[str, Any]:
        """SD 1.5 img2img — upload source image first, then KSampler over VAEEncode."""
        width = min(request.width, self.max_image_width)
        height = min(request.height, self.max_image_height)
        seed = request.seed or random.randint(1, 2**31)

        return {
            "3": {
                "class_type": "KSampler",
                "inputs": {
                    "seed": seed,
                    "steps": request.steps,
                    "cfg": request.guidance_scale,
                    "sampler_name": "euler",
                    "scheduler": "normal",
                    "denoise": request.variation_strength,
                    "model": ["4", 0],
                    "positive": ["6", 0],
                    "negative": ["7", 0],
                    "latent_image": ["11", 0],
                },
            },
            "4": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {"ckpt_name": "v1-5-pruned-emaonly.safetensors"},
            },
            "6": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": request.prompt, "clip": ["4", 1]},
            },
            "7": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "text": request.negative_prompt or "text, watermark, ugly, low quality",
                    "clip": ["4", 1],
                },
            },
            "8": {
                "class_type": "VAEDecode",
                "inputs": {"samples": ["3", 0], "vae": ["4", 2]},
            },
            "9": {
                "class_type": "SaveImage",
                "inputs": {"filename_prefix": "mycel_var", "images": ["8", 0]},
            },
            "10": {
                "class_type": "LoadImage",
                "inputs": {"image": source_filename},
            },
            "11": {
                "class_type": "VAEEncode",
                "inputs": {"pixels": ["10", 0], "vae": ["4", 2]},
            },
        }

    def _build_wan_i2v_workflow(
        self, request: MediaGenerationRequest, source_filename: str
    ) -> Dict[str, Any]:
        """
        Wan 2.1 1.3B Image-to-Video ComfyUI workflow.

        Wan 2.1 1.3B is explicitly documented as requiring ~8GB VRAM for 480P.
        Source: https://github.com/Wan-Video/Wan2.1

        This workflow is constructed natively — no Wan2.1 source is copied.
        The node graph follows the standard ComfyUI Wan i2v API pattern.

        Resolution is hard-capped at 832×480 (landscape) or 480×832 (portrait)
        to stay within the 1.3B model's tested VRAM envelope.

        Output: SaveVideo node → .mp4 bytes retrieved via /view
        """
        # Clamp resolution
        width = min(request.width, self.max_video_width)
        height = min(request.height, self.max_video_height)
        duration = min(request.duration_seconds, self.max_video_duration)
        fps = min(request.fps, 24)
        total_frames = duration * fps
        seed = request.seed or random.randint(1, 2**31)

        # Build the motion/animation prompt
        video_prompt = request.prompt
        if request.motion_prompt:
            video_prompt = f"{request.prompt}. Motion: {request.motion_prompt}"

        return {
            # Wan i2v model loader
            "1": {
                "class_type": "WanVideoModelLoader",
                "inputs": {
                    "model": self.wan_model,
                    "precision": "fp8_e4m3fn",  # memory-efficient fp8 for 8GB
                    "load_device": "offload_device",
                },
            },
            # CLIP vision encoder for image conditioning
            "2": {
                "class_type": "CLIPVisionLoader",
                "inputs": {"clip_name": "clip_vision_h.safetensors"},
            },
            # VAE for Wan
            "3": {
                "class_type": "AutoencoderKLWan",
                "inputs": {"model": ["1", 0]},
            },
            # Load source image
            "4": {
                "class_type": "LoadImage",
                "inputs": {"image": source_filename},
            },
            # CLIP vision encode (image conditioning)
            "5": {
                "class_type": "CLIPVisionEncode",
                "inputs": {"clip_vision": ["2", 0], "image": ["4", 0]},
            },
            # Wan text encode (positive)
            "6": {
                "class_type": "WanTextEncode",
                "inputs": {
                    "text": video_prompt,
                    "model": ["1", 0],
                },
            },
            # Wan text encode (negative)
            "7": {
                "class_type": "WanTextEncode",
                "inputs": {
                    "text": request.negative_prompt or "ugly, blurry, low quality, watermark, text",
                    "model": ["1", 0],
                },
            },
            # Wan i2v conditioning (image + text)
            "8": {
                "class_type": "WanImageToVideoCombine",
                "inputs": {
                    "positive": ["6", 0],
                    "negative": ["7", 0],
                    "image_cond": ["5", 0],
                    "model": ["1", 0],
                    "clip_vision": ["2", 0],
                    "vae": ["3", 0],
                },
            },
            # Empty video latent
            "9": {
                "class_type": "EmptyWanLatentVideo",
                "inputs": {
                    "width": width,
                    "height": height,
                    "batch_size": total_frames,
                    "vae": ["3", 0],
                },
            },
            # KSampler for video
            "10": {
                "class_type": "KSampler",
                "inputs": {
                    "seed": seed,
                    "steps": 20,  # Fewer steps for video to save VRAM time
                    "cfg": 6.0,
                    "sampler_name": "dpmpp_2m",
                    "scheduler": "karras",
                    "denoise": 1.0,
                    "model": ["8", 0],
                    "positive": ["8", 1],
                    "negative": ["8", 2],
                    "latent_image": ["9", 0],
                },
            },
            # VAE decode
            "11": {
                "class_type": "VAEDecodeVideo",
                "inputs": {"samples": ["10", 0], "vae": ["3", 0]},
            },
            # Save video
            "12": {
                "class_type": "SaveVideo",
                "inputs": {
                    "filename_prefix": "mycel_vid",
                    "fps": fps,
                    "images": ["11", 0],
                },
            },
        }

    # ──────────────────────────────────────────────────────────────────────────
    # ComfyUI API helpers
    # ──────────────────────────────────────────────────────────────────────────

    def _get_headers(self) -> Dict[str, str]:
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def _upload_image(self, client: httpx.AsyncClient, image_bytes: bytes) -> str:
        """Upload image bytes to ComfyUI's input directory. Returns the filename."""
        files = {"image": ("source.png", image_bytes, "image/png")}
        res = await client.post(f"{self.base_url}/upload/image", files=files)
        res.raise_for_status()
        return res.json()["name"]

    async def _execute_workflow(self, workflow: Dict[str, Any]) -> bytes:
        """
        Submit workflow to ComfyUI, poll history until complete, download output.
        Works for both image (SaveImage → /view) and video (SaveVideo → /view).
        """
        headers = self._get_headers()

        async with httpx.AsyncClient(timeout=self.timeout, headers=headers) as client:
            # 1. Queue prompt
            try:
                queue_res = await client.post(
                    f"{self.base_url}/prompt", json={"prompt": workflow}
                )
                queue_res.raise_for_status()
                prompt_id = queue_res.json().get("prompt_id")
                if not prompt_id:
                    raise RuntimeError("ComfyUI did not return a prompt_id.")
            except httpx.RequestError as e:
                raise RuntimeError(f"Cannot connect to ComfyUI at {self.base_url}: {e}")

            logger.info(f"ComfyUI queued (prompt_id={prompt_id}). Polling for completion...")

            # 2. Poll history
            poll_interval = 2.0
            elapsed = 0.0

            while elapsed < self.timeout:
                hist_res = await client.get(f"{self.base_url}/history/{prompt_id}")
                hist_res.raise_for_status()
                history = hist_res.json()

                if prompt_id in history:
                    outputs = history[prompt_id].get("outputs", {})

                    # Try SaveVideo node (12) first, then SaveImage (9)
                    for node_id in ("12", "9"):
                        node_output = outputs.get(node_id)
                        if not node_output:
                            continue

                        # SaveVideo outputs "videos", SaveImage outputs "images"
                        items = node_output.get("videos") or node_output.get("images")
                        if not items:
                            continue

                        item = items[0]
                        filename = item["filename"]
                        subfolder = item.get("subfolder", "")
                        item_type = item.get("type", "output")

                        view_url = (
                            f"{self.base_url}/view"
                            f"?filename={filename}&subfolder={subfolder}&type={item_type}"
                        )
                        media_res = await client.get(view_url)
                        media_res.raise_for_status()

                        logger.info(
                            f"ComfyUI generation complete. "
                            f"Downloaded {len(media_res.content)} bytes from node {node_id}."
                        )
                        return media_res.content

                    raise RuntimeError(
                        f"ComfyUI finished (prompt_id={prompt_id}) but no output found in nodes 9 or 12."
                    )

                await asyncio.sleep(poll_interval)
                elapsed += poll_interval

            raise TimeoutError(f"ComfyUI generation timed out after {self.timeout}s.")

    # ──────────────────────────────────────────────────────────────────────────
    # MediaGenerationProvider interface
    # ──────────────────────────────────────────────────────────────────────────

    async def generate_image(self, request: MediaGenerationRequest) -> bytes:
        """TEXT_TO_IMAGE via SD 1.5 txt2img."""
        logger.info(f"ComfyUI generating image: {request.prompt[:60]}...")
        workflow = self._build_txt2img_workflow(request)
        return await self._execute_workflow(workflow)

    async def generate_video(self, request: MediaGenerationRequest) -> bytes:
        """TEXT_TO_VIDEO — not supported on 8GB without a T2V checkpoint."""
        raise CapabilityUnavailableError(
            operation=MediaOperation.TEXT_TO_VIDEO,
            provider="ComfyUIProvider",
            reason=(
                "TEXT_TO_VIDEO requires a dedicated text-to-video model checkpoint "
                "(e.g. Wan 2.1 T2V 14B) which exceeds the 8GB VRAM budget. "
                "Use IMAGE_TO_VIDEO instead: first generate an image, then animate it."
            ),
        )

    async def transform_image(self, request: MediaGenerationRequest) -> bytes:
        """IMAGE_TO_IMAGE via SD 1.5 img2img. Refines an existing image."""
        if not request.source_image_bytes:
            raise ValueError("transform_image requires source_image_bytes in the request.")
        logger.info(f"ComfyUI transforming image: {request.prompt[:60]}...")

        headers = self._get_headers()
        async with httpx.AsyncClient(timeout=self.timeout, headers=headers) as client:
            source_filename = await self._upload_image(client, request.source_image_bytes)

        workflow = self._build_img2img_workflow(request, source_filename)
        return await self._execute_workflow(workflow)

    async def create_variation(self, request: MediaGenerationRequest) -> bytes:
        """IMAGE_VARIATION — produces a new image variant. Original artifact is immutable."""
        if not request.source_image_bytes:
            raise ValueError("create_variation requires source_image_bytes in the request.")
        logger.info(f"ComfyUI generating variation: {request.prompt[:60]}...")

        headers = self._get_headers()
        async with httpx.AsyncClient(timeout=self.timeout, headers=headers) as client:
            source_filename = await self._upload_image(client, request.source_image_bytes)

        workflow = self._build_img2img_workflow(request, source_filename)
        return await self._execute_workflow(workflow)

    async def animate_image(self, request: MediaGenerationRequest) -> bytes:
        """
        IMAGE_TO_VIDEO / IMAGE_ANIMATION via Wan 2.1 1.3B (8GB-compatible).

        The Wan 2.1 1.3B model is explicitly documented to run at ~8GB VRAM
        for 480P resolution. This is the primary video generation path.
        """
        if not request.source_image_bytes:
            raise ValueError("animate_image requires source_image_bytes in the request.")

        logger.info(
            f"ComfyUI animating image → video "
            f"(duration={request.duration_seconds}s, fps={request.fps}): "
            f"{request.prompt[:60]}..."
        )

        headers = self._get_headers()
        async with httpx.AsyncClient(timeout=self.timeout, headers=headers) as client:
            source_filename = await self._upload_image(client, request.source_image_bytes)

        workflow = self._build_wan_i2v_workflow(request, source_filename)
        return await self._execute_workflow(workflow)
