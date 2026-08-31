# Creative Media Generation — Mycel

This document describes the Creative Media Generation system built into Mycel.
It enables Riya Sharma and the Creative Team to generate, transform, and animate
creative media assets using AI — purely by describing what they want, without any
knowledge of underlying models, workflow IDs, or hardware configuration.

---

## Supported Operations

| Operation | Description | Tool | Default Provider |
|---|---|---|---|
| `TEXT_TO_IMAGE` | Generate an image from a text prompt | `creative.media.generate` | ComfyUI → Pollinations |
| `IMAGE_TO_IMAGE` | Refine/improve an existing image | `creative.media.transform` | ComfyUI |
| `IMAGE_VARIATION` | Create variants of an existing image | `creative.media.transform` | ComfyUI → Pollinations |
| `IMAGE_TO_VIDEO` | Animate a still image into a short video | `creative.media.animate` | ComfyUI (Wan 2.1 1.3B) |
| `IMAGE_ANIMATION` | Same as IMAGE_TO_VIDEO with animation defaults | `creative.media.animate` | ComfyUI (Wan 2.1 1.3B) |
| `TEXT_TO_VIDEO` | Generate video from text (8GB budget note) | `creative.media.generate` | ComfyUI → `CAPABILITY_UNAVAILABLE` |
| `MULTI_IMAGE_TO_VIDEO` | Combine multiple images into video | `creative.media.generate` | Provider-dependent |

> [!IMPORTANT]
> `TEXT_TO_VIDEO` returns `CAPABILITY_UNAVAILABLE` on an 8GB VRAM machine without a
> dedicated T2V checkpoint. This is an honest capability boundary, not an error.
> Use `IMAGE_TO_VIDEO` instead: generate an image first, then animate it.

---

## Intent Resolution Examples

| User Says | Resolved Operation | Tool Called |
|---|---|---|
| "Create a futuristic AI hackathon poster" | `TEXT_TO_IMAGE` | `creative.media.generate` |
| "Make this poster more premium" | `IMAGE_TO_IMAGE` | `creative.media.transform` |
| "Create 4 versions of this poster" | `IMAGE_VARIATION` | `creative.media.transform` |
| "Turn this poster into a 5 second reel" | `IMAGE_TO_VIDEO` | `creative.media.animate` |
| "Animate this product photo" | `IMAGE_ANIMATION` | `creative.media.animate` |
| "Create a cinematic futuristic city scene" | `TEXT_TO_VIDEO` | `creative.media.generate` → `CAPABILITY_UNAVAILABLE` |
| "Use these 3 photos for a product showcase" | `MULTI_IMAGE_TO_VIDEO` | `creative.media.generate` |

---

## Provider Abstraction

```
Riya (Agent)
     │  "Create a promo image for Python classes"
     ▼
Creative Intent (TaskIntent with media_operation = TEXT_TO_IMAGE)
     │
     ▼
creative.media.generate (Tool)
     │
     ▼
Security Gateway → ArmorIQ
     │  Intent: "Creative media generation: TEXT_TO_IMAGE for social_media"
     ▼
MediaGenerationProvider (interface)
     ├── ComfyUIProvider  (primary — local GPU, SD 1.5 / Wan 2.1)
     └── PollinationsProvider  (fallback — free remote, FLUX, images only)
     │
     ▼
ArtifactService → Cloudinary → ArtifactReference
```

Riya never sees provider names, model names, or workflow IDs.
She receives an `ArtifactReference` with a URL.

---

## ArmorIQ Semantic Intent

The Security Gateway sends ArmorIQ a **semantic intent string** — not a raw API call.

| Tool Called | ArmorIQ Sees |
|---|---|
| `creative.media.generate` | `"Creative media generation: TEXT_TO_IMAGE for social_media — emp_riya_sharma task=task_xyz"` |
| `creative.media.animate` | `"Creative media animation: IMAGE_TO_VIDEO of artifact art_abc (5s) — emp_riya_sharma task=task_xyz"` |
| `creative.media.transform` | `"Creative media transformation: IMAGE_VARIATION of artifact art_abc — emp_riya_sharma task=task_xyz"` |

This allows ArmorIQ to evaluate **what is being created** and **for whom**, not just which code path executed.

---

## ComfyUI Integration

Mycel communicates with ComfyUI via its HTTP API. **ComfyUI is external — it is NOT embedded in Mycel.**

### Image Generation (SD 1.5)

Standard Stable Diffusion 1.5 txt2img workflow. Optimised for 8GB VRAM:
- **Max resolution**: 1024×1024 (hard cap)
- **Batch size**: Always 1
- **Model**: `v1-5-pruned-emaonly.safetensors`
- **Steps**: 25 default

### Image-to-Video Generation (Wan 2.1 1.3B)

Wan 2.1 1.3B is an open-source image-to-video model explicitly documented to run
at ~8GB VRAM for 480P resolution (source: [Wan2.1 GitHub](https://github.com/Wan-Video/Wan2.1)).

> [!IMPORTANT]
> **Do NOT use the Wan 2.1 14B model on an 8GB machine.**
> Only the **1.3B** variant is confirmed to work at 480P.

Wan 2.1 1.3B video defaults:
- **Max resolution**: 832×480 (480P)
- **Max duration**: 8 seconds
- **Default FPS**: 16
- **Default steps**: 20 (fewer than image for VRAM efficiency)
- **Precision**: `fp8_e4m3fn` (memory-efficient 8-bit float)

### ComfyUI Setup (for video generation)

1. Install ComfyUI externally — **never clone it into Mycel**
2. Download `wan2.1-i2v-1.3B-480P.safetensors` → place in `ComfyUI/models/checkpoints/`
3. Download CLIP vision: `clip_vision_h.safetensors` → place in `ComfyUI/models/clip_vision/`
4. Configure in `.env`:
   ```env
   COMFYUI_BASE_URL=http://127.0.0.1:8188
   COMFYUI_TIMEOUT_SECONDS=180
   COMFYUI_WAN_MODEL=wan2.1-i2v-1.3B-480P.safetensors
   COMFYUI_VIDEO_DEFAULT_FPS=16
   COMFYUI_VIDEO_MAX_DURATION=8
   ```

---

## 8GB VRAM Considerations

| Operation | Model | VRAM Usage | Notes |
|---|---|---|---|
| `TEXT_TO_IMAGE` | SD 1.5 | ~4–5GB | Comfortable within budget |
| `IMAGE_VARIATION` | SD 1.5 img2img | ~4–5GB | Comfortable within budget |
| `IMAGE_TO_VIDEO` | Wan 2.1 1.3B | ~7–8GB | Near limit; fp8 precision required |
| `TEXT_TO_VIDEO` | Not supported | >8GB | Returns `CAPABILITY_UNAVAILABLE` |

Guardrails enforced:
- `batch_size = 1` always
- Image max: 1024×1024
- Video max: 832×480 (480P), 8 seconds
- No concurrent heavy generations (use existing task execution system)

---

## Artifact Flow

```
MediaGenerationProvider returns raw bytes (PNG or MP4)
     │
     ▼
Tool writes bytes to temp file
     │
     ▼
ArtifactService.create_and_store()
     ├── ArtifactValidator (MIME type, file size, existence)
     ├── SHA-256 checksum
     └── CloudinaryStorage.upload()
           │
           ▼
     Cloudinary CDN
           │
           ▼
     ArtifactReference (artifact_id, secure_url, type, size_bytes)
           │
           ▼
     Returned to Riya as ToolResult.output["artifact"]
```

**Original artifacts are always immutable.** Variations and transformations produce
new artifacts with `parent_artifact_id` set to preserve lineage.

---

## Security Flow

```
Riya wants to animate a poster
     │
     ▼
creative.media.animate (Tool)
     │ validate: source_artifact_id is not a raw filesystem path
     │ validate: artifact exists and belongs to current task context
     ▼
CoreToolGateway
     ├── ToolSecurityPolicy.validate_request() (tool in allowed_tools)
     └── SecurityGateway.evaluate_request()
           ├── IntentValidator — is this a coherent creative request?
           ├── PolicyEngine — is emp_riya_sharma allowed creative.media.animate?
           ├── RiskEngine — what is the risk level of IMAGE_TO_VIDEO?
           └── ArmorIQ — semantic intent check
                 │ "Creative media animation: IMAGE_TO_VIDEO of art_abc (5s)"
                 ▼
           ALLOW / DENY
     │
     ▼
ComfyUIProvider.animate_image()
```

No raw filesystem paths are accepted as media inputs.
All artifact access goes through `ArtifactService`.

---

## Failure Handling

| Failure Mode | Response |
|---|---|
| ComfyUI offline | Fallback to Pollinations (images) or `status=error` (video) |
| VRAM out of memory (OOM) | ComfyUI error propagated as `status=error` |
| `TEXT_TO_VIDEO` requested | `status=capability_unavailable` (never fake success) |
| Invalid/missing artifact ID | `status=error` with descriptive message |
| Raw path detected | `status=error` — Security violation logged |
| Cloudinary upload failure | `status=error` — temp file cleaned up |
| ComfyUI timeout | `TimeoutError` wrapped in `status=error` |

---

## Live Tests

Live tests require a running ComfyUI instance and the appropriate model checkpoints.

```bash
# Enable live tests
$env:COMFYUI_LIVE_TEST="true"
$env:SECURITY_PROVIDER_MODE="mock"
$env:PYTHONPATH="."

# Live Test 1: Text → Image
python test_riya.py
# Prompt: "Create a clean futuristic technology event poster with professional typography"
# Expected: image artifact saved locally and to Cloudinary

# Live Test 2: Image → Video (use artifact_id from Test 1)
python test_riya.py
# Prompt: "Animate this poster into a 5 second promotional animation with slow zoom"
# Expected: video artifact

# Live Test 3: Text → Video (should return CAPABILITY_UNAVAILABLE)
python test_riya.py
# Prompt: "Create a cinematic futuristic city scene video"
# Expected: status=capability_unavailable (NOT a failure — an honest boundary)
```

---

## Repository Cleanliness Verification

After implementation, verify no repositories were vendored:

```bash
grep -r "OpenMontage\|Wan2.1\|AnimateDiff\|git submodule\|vendor" backend/ \
  --include="*.py" --include="*.txt" --include="*.toml"
# Expected: zero results
```

✅ No repositories cloned  
✅ No repositories vendored  
✅ No submodules added  
✅ ComfyUI workflows constructed natively in Python  
✅ Mycel is the source of truth
