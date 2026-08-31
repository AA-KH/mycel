# ComfyUI Image Generation Integration

This document outlines the local ComfyUI provider integration designed to provide real image generation capabilities to the Mycel platform, specifically tailored for the Creative Team (Riya Sharma).

## Architecture

The integration follows a strict layered architecture to ensure that agents do not directly access ComfyUI internals, ensuring all generation requests pass through Mycel's security and policy enforcement gates.

```mermaid
graph TD
    A[Agent: Riya] -->|Executes Tool| B(Image Generation Tool)
    B --> C{Security Gateway / ArmorIQ}
    C -->|Approved| D[Tool Registry]
    D --> E[ImageGenerationProvider]
    E --> F[ComfyUIProvider]
    F -->|HTTP POST /prompt| G[Local ComfyUI API]
    G --> H[Local GPU (8GB VRAM)]
    H -->|HTTP GET /view| F
    F --> I[Artifact System]
    I --> J[(Cloudinary)]
    J -->|ArtifactReference| A
```

## Hardware Assumptions & 8GB VRAM Constraint

The primary development constraint is an 8GB VRAM limit. The implementation enforces the following guardrails:
- **Maximum Resolution**: Hard capped at 1024x1024 (default 512x512).
- **Batch Size**: Strictly `1`.
- **Concurrency**: Bounded, executing synchronously per request.
- **Model Target**: Standard Stable Diffusion 1.5 checkpoints (e.g., `v1-5-pruned-emaonly.safetensors`).

## Setup and Installation

Mycel does **not** install ComfyUI automatically. It expects ComfyUI to be managed externally.

1. Install [ComfyUI](https://github.com/comfyanonymous/ComfyUI) on your machine.
2. Download an SD 1.5 model (e.g., `v1-5-pruned-emaonly.safetensors`) and place it in your ComfyUI `models/checkpoints/` directory.
3. Start ComfyUI (by default, it binds to `http://127.0.0.1:8188`).
4. In your Mycel backend `.env` file, configure the provider:
   ```env
   COMFYUI_BASE_URL=http://127.0.0.1:8188
   COMFYUI_TIMEOUT_SECONDS=120
   COMFYUI_MAX_RETRIES=2
   COMFYUI_DEFAULT_WIDTH=512
   COMFYUI_DEFAULT_HEIGHT=512
   COMFYUI_DEFAULT_STEPS=25
   COMFYUI_LIVE_TEST=false
   ```
5. Riya can now automatically generate real images using the `image.generate` tool!

## Fallback & Graceful Degradation

If ComfyUI is not running or the connection is refused, the `ComfyUIProvider` throws an exception which is caught by the tool implementation. The tool gracefully falls back to returning a "stub generation" artifact containing a placeholder URL (`cloudinary://mycel/assets/stub_generation.png`), ensuring that pipeline execution does not crash during CI/CD or offline development.

## Image Variation (img2img)

Image variation uses a dynamic img2img workflow construction. It temporarily uploads the source image bytes to the ComfyUI API (`/upload/image`) before executing the `KSampler` over the `VAEEncode`'d latent representations, utilizing a normalized `variation_strength` mapping to the sampler's `denoise` parameter.
