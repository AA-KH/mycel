# PrismMotion Extraction Matrix

This document maps the concepts and implementations from the `PrismMotion-EvolveAI` reference repository to their new integrated home within the Mycel architecture.

| SOURCE COMPONENT | REUSABLE CONCEPT | MYCEL TARGET | ACTION | REASON |
|---|---|---|---|---|
| `stage1_scenes.py` | Scene generation | Creative pipelines (e.g., `creative_video`) | ADAPT | Replaces manual scripting with a defined pipeline step using standard LLM reasoning. |
| `stage2_moa_manim.py` | Technical Animation | `creative.technical_animation.render` Tool | ADAPT | Decoupled from hardcoded stages to allow intent-based resolution for Arjun. |
| `stage2_remotion.py` | Programmatic UI animation | `media.video.compose` | ADAPT | Integrated as a generic composition tool rather than a mandatory Remotion pipeline. |
| `stage3_script.py` | Narration | `creative.speech.generate` Tool | ADAPT | Reuses Mycel standard TTS pipeline. |
| `stage4_tts.py` | Azure/OpenAI TTS | `creative.speech.generate` Tool | ADAPT | Merged into the global TTS provider abstraction. |
| `utils/pexels_client.py` | Stock Video Search | `creative.stock_media.search` Tool | ADAPT | Decoupled so any creative member can use it. |
| `doctor_ad_stages/` | Ad Video Workflow | Declarative `TeamPipeline` | ADAPT | Replaced hardcoded scripts with a declarative pipeline definition in Mycel. |
| `creator_mode.py` | UI/WebSocket progress | Existing Realtime Infrastructure | DISCARD/REUSE | Mycel already has execution context and realtime WebSocket reporting. |
| `compliance_stages/` | Pharma-specific logic | N/A | DISCARD | Domain-specific logic not relevant to a general Creative Media Specialist. |
| `app/main.py` | FastAPI app | N/A | DISCARD | Mycel has its own routing and architecture. |
| `app/db.py` | Database handling | N/A | DISCARD | Mycel uses MongoDB/Cloudinary for Artifacts and memory. |

## Extraction Principles Applied
1. **No Duplication:** We did not import PrismMotion's job queue, database, or WebSocket handling. We used Mycel's Task Orchestrator.
2. **Provider Agnostic:** We formalized `creative.stock_media.search` and `media.video.generate` as tools, allowing us to swap Pexels or ComfyUI implementations cleanly.
3. **Intent Resolution:** Instead of direct LLM tool selection for "use manim", Arjun now resolves "I need a technical explainer", which resolves to `MediaOperation.TECHNICAL_ANIMATION`, which triggers the correct tool.
