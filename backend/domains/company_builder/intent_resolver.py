import json
import logging
from typing import Optional
from core.groq_engine import groq_engine
from tasks.models import OutputSpec, OutputModality, ArtifactType, PreviewType

logger = logging.getLogger(__name__)

class IntentResolver:
    """
    Resolves a user's natural language request into a structured OutputSpec.
    Distinguishes intent, output modality, and artifact type.
    """

    def resolve(self, prompt: str) -> OutputSpec:
        """
        Synchronous wrapper if needed, but normally use async resolve_async.
        """
        import asyncio
        return asyncio.run(self.resolve_async(prompt))

    async def resolve_async(self, prompt: str) -> OutputSpec:
        # 1. Deterministic Mappings (Fast Path)
        deterministic_spec = self._apply_deterministic_rules(prompt)
        if deterministic_spec:
            return deterministic_spec

        # 2. Semantic LLM Mappings (Fallback)
        return await self._apply_llm_resolution(prompt)

    def _apply_deterministic_rules(self, prompt: str) -> Optional[OutputSpec]:
        """
        Hardcoded intent resolution to avoid LLM latency for obvious requests.
        """
        prompt_lower = prompt.lower()
        
        # Determine if it's a "create/build/make" intent rather than "explain/review"
        is_generation = any(verb in prompt_lower for verb in ["create", "build", "make", "generate"])
        is_explaining = any(verb in prompt_lower for verb in ["explain", "analyze", "review", "suggest", "ideas"])
        
        if is_explaining:
            return OutputSpec(
                intent="ANALYSIS_REPORT",
                modality=OutputModality.REPORT,
                artifact_type=ArtifactType.RESEARCH_REPORT,
                required_capabilities=["RESEARCH"],
                preview_type=PreviewType.DOCUMENT_VIEWER,
                generation_required=True
            )

        if "landing page" in prompt_lower or "website" in prompt_lower or "homepage" in prompt_lower or "web page" in prompt_lower:
            return OutputSpec(
                intent="CREATE_WEBSITE",
                modality=OutputModality.WEBSITE,
                artifact_type=ArtifactType.LANDING_PAGE if "landing" in prompt_lower else ArtifactType.WEBSITE,
                required_capabilities=["WEB_DEVELOPMENT"],
                preview_type=PreviewType.LIVE_WEBSITE,
                generation_required=True
            )
            
        if "poster" in prompt_lower or "logo" in prompt_lower or "image" in prompt_lower or "graphic" in prompt_lower:
            artifact = ArtifactType.LOGO if "logo" in prompt_lower else (ArtifactType.POSTER if "poster" in prompt_lower else ArtifactType.ILLUSTRATION)
            return OutputSpec(
                intent="CREATE_IMAGE",
                modality=OutputModality.IMAGE,
                artifact_type=artifact,
                required_capabilities=["DESIGN"],
                preview_type=PreviewType.IMAGE,
                generation_required=True
            )
            
        if "pitch deck" in prompt_lower or "presentation" in prompt_lower or "ppt" in prompt_lower:
            return OutputSpec(
                intent="CREATE_PRESENTATION",
                modality=OutputModality.PRESENTATION,
                artifact_type=ArtifactType.PITCH_DECK,
                required_capabilities=["DESIGN", "COPYWRITING"],
                preview_type=PreviewType.SLIDE_VIEWER,
                generation_required=True
            )

        return None

    async def _apply_llm_resolution(self, prompt: str) -> OutputSpec:
        """
        Uses an LLM to semantically determine the correct OutputSpec.
        """
        system_prompt = (
            "You are an Intent Resolution Engine. "
            "Analyze the user's request and output a strictly typed JSON object matching the OutputSpec schema. "
            "DO NOT output any markdown, only raw JSON.\n\n"
            "Schema:\n"
            "{\n"
            '  "intent": "string (e.g. CREATE_LANDING_PAGE)",\n'
            '  "modality": "WEBSITE | TEXT | IMAGE | AUDIO | VIDEO | CODE | DOCUMENT | SPREADSHEET | PRESENTATION | DATA | REPORT",\n'
            '  "artifact_type": "LOGO | POSTER | BANNER | SOCIAL_MEDIA_CREATIVE | ILLUSTRATION | VIDEO | WEBSITE | LANDING_PAGE | MARKETING_WEBSITE | PROMOTIONAL_WEBSITE | PITCH_DECK | RESEARCH_REPORT | FINANCIAL_MODEL | FINANCIAL_FEASIBILITY_REPORT | LEGAL_ASSESSMENT | FEASIBILITY_REPORT | MARKET_RESEARCH_REPORT | CODE_BUNDLE | DOCUMENT",\n'
            '  "required_capabilities": ["WEB_DEVELOPMENT" or "DESIGN" or "RESEARCH" etc.],\n'
            '  "preview_type": "IMAGE | LIVE_WEBSITE | SLIDE_VIEWER | PDF_VIEWER | VIDEO_PLAYER | AUDIO_PLAYER | DOCUMENT_VIEWER | SPREADSHEET_VIEWER | CODE_VIEWER | NONE",\n'
            '  "generation_required": true\n'
            "}\n\n"
            "Rules:\n"
            "1. If they ask to build/create an online presence, landing page, or website, modality MUST be WEBSITE.\n"
            "2. If they ask for analysis, review, or explanation, modality MUST be REPORT.\n"
        )
        
        try:
            response = await groq_engine.chat_completion(
                model="qwen/qwen3.8-27b",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            raw = response.choices[0].message.content or "{}"
            
            # Clean markdown
            if raw.startswith("```json"): raw = raw[7:]
            if raw.startswith("```"): raw = raw[3:]
            if raw.endswith("```"): raw = raw[:-3]
                
            data = json.loads(raw.strip())
            
            return OutputSpec(
                intent=data.get("intent", "UNKNOWN_TASK"),
                modality=OutputModality(data.get("modality", "REPORT")),
                artifact_type=ArtifactType(data.get("artifact_type", "DOCUMENT")),
                required_capabilities=data.get("required_capabilities", []),
                preview_type=PreviewType(data.get("preview_type", "NONE")),
                generation_required=data.get("generation_required", True)
            )
        except Exception as e:
            logger.error(f"Semantic LLM resolution failed: {e}. Falling back to default REPORT.")
            return OutputSpec(
                intent="GENERIC_TASK",
                modality=OutputModality.REPORT,
                artifact_type=ArtifactType.DOCUMENT,
                required_capabilities=["RESEARCH"],
                preview_type=PreviewType.DOCUMENT_VIEWER,
                generation_required=True
            )
