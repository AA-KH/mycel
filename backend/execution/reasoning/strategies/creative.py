"""
Creative Review Strategy — Mycel Reasoning Engine

This strategy drives Riya Sharma's reasoning for all creative media tasks.
It upgrades the basic image-generation loop into a full creative media
intent resolver capable of handling:

    TEXT_TO_IMAGE       — "Create a futuristic AI hackathon poster"
    IMAGE_TO_IMAGE      — "Make this poster look more premium"
    IMAGE_VARIATION     — "Create 4 versions of this poster"
    IMAGE_TO_VIDEO      — "Animate this poster into a 5 second Instagram reel"
    IMAGE_ANIMATION     — "Bring this product photo to life with subtle motion"
    TEXT_TO_VIDEO       — "Create a cinematic futuristic city scene" (may be UNAVAILABLE)
    MULTI_IMAGE_TO_VIDEO — "Turn these product photos into a showcase reel"

Design principles:
    - Riya thinks in USER INTENT, not in tools or workflows
    - One image → one tool call → final_answer (no over-generation)
    - CAPABILITY_UNAVAILABLE is a valid, honest final answer
    - Never hallucinate additional tool calls after receiving an artifact
"""

from typing import Dict, Any, List, Literal, Optional
from pydantic import BaseModel

from .base import ReasoningStrategy
from ..models import TaskIntent, Plan, Critique
from ..context import ReasoningContext


# ─────────────────────────────────────────────────────────────────────────────
# Intent routing reference (for system prompt injection)
# ─────────────────────────────────────────────────────────────────────────────

_INTENT_ROUTING_GUIDE = """
MEDIA OPERATION ROUTING (resolve ONE operation per task):

    "create a poster / image / graphic / banner / design"
    → media_operation = TEXT_TO_IMAGE
    → output_artifact_type = image
    → tool = creative.media.generate

    "make this look better / refine this image / improve this design"
    → media_operation = IMAGE_TO_IMAGE
    → output_artifact_type = image
    → tool = creative.media.transform
    → requires: input_artifact_ids (source image)

    "create N versions / variations / alternatives of this"
    → media_operation = IMAGE_VARIATION
    → output_artifact_type = image
    → tool = creative.media.transform
    → requires: input_artifact_ids (source image)

    "animate this / turn this into a video / create a reel from this image"
    → media_operation = IMAGE_TO_VIDEO or IMAGE_ANIMATION
    → output_artifact_type = video
    → tool = creative.media.animate
    → requires: input_artifact_ids (source image)

    "create a video / generate a cinematic scene / make a promo video from scratch"
    → media_operation = TEXT_TO_VIDEO
    → output_artifact_type = video
    → tool = creative.media.generate
    → NOTE: may return CAPABILITY_UNAVAILABLE (no T2V model on 8GB GPU)

    "use these images to create a video / product showcase / slideshow"
    → media_operation = MULTI_IMAGE_TO_VIDEO
    → output_artifact_type = video
    → tool = creative.media.generate
    → requires: multiple input_artifact_ids

TOOL MAPPING:
    creative.media.generate  — Creates from scratch (text → image or text → video)
    creative.design.layout   — Structures HTML/CSS typography over a background image
    creative.media.transform — Transforms/varies an existing image
    creative.media.animate   — Animates a still image into a video

CRITICAL RULES FOR tool ARGUMENTS:
    - Always include "operation" in tool arguments (e.g. "operation": "TEXT_TO_IMAGE")
    - For image prompts: be highly descriptive, include text/typography explicitly
      (e.g. 'with the text "Join Now!" in bold sans-serif at the top')
    - For animation: include "motion_prompt" (e.g. "slow zoom in, particles floating")
    - For video: include "duration_seconds" (default 5, max 8)
    - NEVER include filesystem paths, model names, or ComfyUI details in arguments

FINAL ANSWER RULES:
    - Once an artifact is in the observations, set action = final_answer IMMEDIATELY
    - Do NOT call another tool after receiving a successful artifact
    - If the observation shows CAPABILITY_UNAVAILABLE, that IS your final answer
    - If the observation shows an artifact URL, that IS your final answer
"""

_IMAGE_PROMPT_GUIDE = """
PROMOTIONAL / BANNER IMAGE PROMPT CONSTRUCTION:
    - Background Generation: Use `creative.media.generate` (TEXT_TO_IMAGE) for the background. Do NOT include explicit text in the background prompt. 
    - Layout & Typography: Use `creative.design.layout` to structure text over the generated background.
    - Write clean, responsive HTML/CSS using absolute positioning or flexbox to place text perfectly.
    - Use premium web fonts (e.g. Inter, Playfair Display, Montserrat - they are auto-injected).
    - Provide the background artifact ID to `creative.design.layout` so it composites them together.
    - Example prompt for background: "Sleek modern tech workspace background, featuring abstract geometric tech patterns in electric blue and white, dark background, modern professional style."
    - Example layout HTML: "<div class='banner'><h1>Live Python Batch Classes</h1><p>Join Now</p></div>"
"""


# ─────────────────────────────────────────────────────────────────────────────
# Strategy
# ─────────────────────────────────────────────────────────────────────────────

class CreativeReviewStrategy(ReasoningStrategy):
    """
    Creative workflow: Understand Intent → Resolve Operation → Execute → Deliver.

    One tool call per deliverable. No over-generation. No speculative loops.
    """

    async def understand(
        self, task: Dict[str, Any], context: ReasoningContext, system_prompt: str
    ) -> TaskIntent:
        system_prompt += (
            "\n\nYou are a Creative Director AI. Your job is to understand exactly what "
            "creative output the user wants and resolve it into a structured TaskIntent.\n\n"
            + _INTENT_ROUTING_GUIDE
        )

        prompt = (
            f"Task: {task.get('description', '')}\n\n"
            "Analyze this creative request carefully and produce a TaskIntent with:\n"
            "- goal: a clear one-sentence statement of what needs to be created\n"
            "- output_type: 'image' or 'video'\n"
            "- media_operation: the SINGLE most appropriate operation from the routing guide\n"
            "- output_artifact_type: 'image' or 'video'\n"
            "- input_artifact_ids: list any artifact IDs the user mentioned (empty if none)\n"
            "- media_metadata: dict with any relevant: duration_seconds, fps, motion_prompt, "
            "aspect_ratio, style, purpose\n"
            "- constraints: important requirements (8GB VRAM limit, single image output, etc.)\n"
            "- required_capabilities: the creative skills needed\n"
        )
        return await self.llm.generate_structured(system_prompt, prompt, TaskIntent)

    async def decompose_and_plan(
        self, intent: TaskIntent, context: ReasoningContext, system_prompt: str
    ) -> Plan:
        operation = intent.media_operation or "TEXT_TO_IMAGE"
        output_type = intent.output_artifact_type or "image"

        if operation in ("IMAGE_TO_VIDEO", "IMAGE_ANIMATION", "MULTI_IMAGE_TO_VIDEO"):
            plan_guidance = (
                "The user wants a VIDEO from existing image(s). Plan exactly ONE step:\n"
                "  Step 1: Use creative.media.animate to animate the source image into a video.\n"
                "Do NOT add extra image generation steps unless no source image was provided."
            )
        elif operation in ("IMAGE_TO_IMAGE", "IMAGE_VARIATION"):
            plan_guidance = (
                "The user wants to TRANSFORM or VARY an existing image. Plan exactly ONE step:\n"
                "  Step 1: Use creative.media.transform with the source image.\n"
                "Do NOT generate a new image from scratch."
            )
        elif operation == "TEXT_TO_VIDEO":
            plan_guidance = (
                "The user wants a TEXT-TO-VIDEO generation. Plan exactly ONE step:\n"
                "  Step 1: Use creative.media.generate with operation=TEXT_TO_VIDEO.\n"
                "This may return CAPABILITY_UNAVAILABLE — that is acceptable and honest."
            )
        else:
            # TEXT_TO_IMAGE (default)
            plan_guidance = (
                "The user wants a single image/graphic created from a text description. "
                "Plan exactly ONE step:\n"
                "  Step 1: Use creative.media.generate with operation=TEXT_TO_IMAGE.\n"
                "Do NOT add multiple image generation steps. One image, one tool call."
            )

        system_prompt += f"\n\nPLANNING GUIDANCE:\n{plan_guidance}"
        prompt = (
            f"Goal: {intent.goal}\n"
            f"Operation: {operation}\n"
            f"Output: {output_type}\n"
            f"Constraints: {intent.constraints}\n\n"
            "Create a minimal, focused execution plan with only the steps described above."
        )
        return await self.llm.generate_structured(system_prompt, prompt, Plan)

    async def decide_next_action(
        self, context: ReasoningContext, system_prompt: str
    ) -> Dict[str, Any]:

        class NextAction(BaseModel):
            action: Literal["tool_call", "final_answer"]
            details: Dict[str, Any]

        intent = context.intent
        operation = (intent.media_operation or "TEXT_TO_IMAGE") if intent else "TEXT_TO_IMAGE"
        output_type = (intent.output_artifact_type or "image") if intent else "image"
        media_meta = (intent.media_metadata or {}) if intent else {}

        system_prompt += (
            "\n\nYou are deciding the NEXT ACTION in a creative media generation task.\n\n"
            + _INTENT_ROUTING_GUIDE
            + "\n\n"
            + _IMAGE_PROMPT_GUIDE
            + "\n\n"
            f"Current operation: {operation}\n"
            f"Expected output type: {output_type}\n"
            f"Media metadata: {media_meta}\n"
        )

        prompt = (
            f"{context.to_llm_context()}\n\n"
            "DECISION RULES (follow strictly):\n"
            "1. If the observations show a successful artifact (contains 'artifact_id' or 'artifact' key), "
            "set action='final_answer' IMMEDIATELY. Do NOT call another tool.\n"
            "2. If the observations show 'capability_unavailable', "
            "set action='final_answer' with the capability error details.\n"
            "3. If no tool has been called yet, call the appropriate tool ONCE.\n"
            "4. NEVER call the same tool twice unless an error occurred.\n\n"
            "If action='tool_call', details MUST contain:\n"
            "  - tool_name: one of 'creative.media.generate', 'creative.media.transform', "
            "'creative.media.animate'\n"
            "  - arguments: dict with 'prompt', 'operation', and any relevant media params\n\n"
            "If action='final_answer', details MUST contain:\n"
            "  - artifact_id (if successful) OR capability_error (if unavailable)\n"
            "  - artifact_url (if available in observations)\n"
            "  - operation_performed\n"
            "  - prompt_used (the prompt that was sent to the tool)\n"
        )

        result = await self.llm.generate_structured(system_prompt, prompt, NextAction)
        return {"action": result.action, "details": result.details}

    async def critique(
        self, context: ReasoningContext, system_prompt: str
    ) -> Critique:
        system_prompt += (
            "\n\nCritique the creative media generation result.\n"
            "Key questions:\n"
            "- Was an artifact successfully generated? (check observations for artifact_id)\n"
            "- Was CAPABILITY_UNAVAILABLE returned? (this is a valid, honest result — status=proceed)\n"
            "- Did a genuine error occur that should be retried? (status=needs_revision)\n"
            "- Is the task complete? If yes, status MUST be 'proceed' so we can deliver the result.\n"
            "DO NOT mark 'needs_revision' if an artifact or CAPABILITY_UNAVAILABLE was returned.\n"
        )
        prompt = f"{context.to_llm_context()}\nCritique the current state and decide next status."
        return await self.llm.generate_structured(system_prompt, prompt, Critique)

    async def verify(
        self,
        final_output: Dict[str, Any],
        context: ReasoningContext,
        system_prompt: str,
    ) -> bool:
        class Verification(BaseModel):
            passed: bool
            reasoning: str

        prompt = (
            f"Goal: {context.intent.goal if context.intent else 'Creative media generation'}\n"
            f"Output: {final_output}\n\n"
            "Verification rules:\n"
            "- PASS if output contains an artifact_id (image or video was created)\n"
            "- PASS if output contains 'capability_unavailable' (honest capability signal)\n"
            "- FAIL only if output is empty or indicates an unexpected system error\n"
        )
        res = await self.llm.generate_structured(system_prompt, prompt, Verification)
        return res.passed
