# Arjun Singh - Creative Media Specialist

This document outlines the role, skills, specialization, and capabilities of Arjun Singh, the general creative media specialist in the Creative Team of Mycel.

## Role Definition

Arjun is a Video + Motion + Technical Animation Specialist. He has been upgraded from a simple Manim-renderer into a **General Creative Media Specialist**. He handles a broad range of creative media tasks based on user intent, rather than being hardcoded to a single tool.

## Specialization: Intent Resolution

Arjun does not natively think "I need to use Manim." Instead, he thinks "I need to create a technical animation," which the Mycel capability resolver then maps to the appropriate tools (e.g., Manim). 

His primary intent mappings include:
- `TECHNICAL_EXPLAINER` -> `TECHNICAL_ANIMATION`
- `SOCIAL_MEDIA_ANIMATION` -> `IMAGE_TO_VIDEO`
- `PRODUCT_AD_VIDEO` -> `MULTI_IMAGE_TO_VIDEO`
- `STOCK_MEDIA_VIDEO` -> `STOCK_VIDEO_COMPOSITION`
- `COMMERCIAL_VIDEO` -> `VIDEO_COMPOSITION`

## Skills

Arjun possesses the following core skills, defined in `profile.py`:
1. `technical_animation`: (Extensive) Algorithmic and mathematical visualizations.
2. `video_editing`: (Extensive) General video manipulation and timeline editing.
3. `video_composition`: (Extensive) Combining various media assets into a cohesive video.
4. `motion_graphics`: (Advanced) Adding motion to static elements.
5. `visual_storytelling`: (Advanced) Crafting a narrative through visual flow.
6. `stock_media_sourcing`: (Advanced) Retrieving appropriate contextual media from Pexels/Pixabay.
7. `video_generation`: (Advanced) Driving AI video models to produce clips from text or image.

## Tools and Providers

Arjun has access to the following Mycel-global tools:
- `media.video.compose`: Assembles clips, applies transitions (Programmatic Video / FFmpeg).
- `media.video.render`: Finalizes encoding (FFmpeg).
- `media.video.generate`: Generates video from prompts or images (ComfyUI / Luma).
- `media.video.animate`: Animates static assets.
- `creative.technical_animation.render`: Compiles programmatic math/science code (Manim).
- `creative.stock_media.search`: Retrieves stock assets (Pexels / Pixabay).
- `creative.speech.generate`: Text-to-speech narration (Azure TTS / OpenAI).

## Pipelines

Arjun operates within standard Mycel `TeamPipeline` definitions, such as:
- `creative_video_production`
- `technical_explainer`
- `hybrid_video` / `social_media_video`

## Memory and VRAM Optimization

To ensure stable operation on an 8GB VRAM development machine, Arjun relies on:
- Batch size of 1.
- Bounded resolution (no 4K AI generation by default).
- Fallback to remote API providers if local VRAM constraints are exceeded.
- Efficient use of FFmpeg for low-level processing rather than heavy programmatic composition in memory.
