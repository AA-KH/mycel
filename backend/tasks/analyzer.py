"""
Task Analyzer (Phase 10 Task Orchestration)

Responsibilities:
- Normalizes raw user request into clean, actionable text while preserving original_request.
- Derives TaskOutcome (objective, intent, success_definition, requested_outputs).
- Detects ambiguous or underspecified requests and generates TaskClarification objects.
- Does NOT perform employee hiring, agent creation, or tool execution.
"""

import re
import uuid
import logging
from typing import Tuple, List, Optional
from tasks.models import (
    TaskRequest,
    TaskOutcome,
    TaskConstraints,
    TaskClarification,
    ClarificationStatus,
)

logger = logging.getLogger(__name__)

KNOWN_OUTPUT_KEYWORDS = {
    "video": ["video", "promo video", "promotional video", "reel", "animation"],
    "image": ["image", "logo", "banner", "graphics", "visual"],
    "research_report": ["research", "competitor analysis", "market research", "investigate", "study"],
    "landing_page": ["landing page", "website", "frontend", "webpage", "ui"],
    "software": ["software", "backend", "api", "app", "code", "bug fix", "feature"],
    "legal_review": ["legal", "contract", "compliance", "terms", "policy"],
    "financial_analysis": ["financial", "finance", "budget", "cost analysis", "forecast"],
    "campaign": ["marketing campaign", "campaign", "social media plan", "content strategy"],
    "operations_plan": ["operations", "workflow", "process plan", "logistics"],
}


class TaskAnalyzer:
    """
    Analyzes user task requests:
    1. Normalizes raw natural language request.
    2. Extracts structured TaskOutcome.
    3. Flags ambiguous requests for user clarification.
    """

    def normalize_request(self, original_request: str) -> str:
        """
        Cleans and normalizes natural language user request without destroying meaning.
        Original request must ALWAYS be preserved separately in Task.original_request.
        """
        if not original_request or not original_request.strip():
            return ""

        text = original_request.strip()

        # Remove prompt injection style commands if present in raw input
        text = re.sub(r'(?i)ignore (all|any)\b.*', '', text).strip()

        # Clean multiple spaces/newlines
        text = re.sub(r'\s+', ' ', text)

        # Normalize common informal intros
        informal_prefixes = [
            r'^(bhai|bro|hey|hello|please|can you|could you|i want to|i need to|we need to)\s+',
            r'^(make|create|build|generate|do|run)\s+me\s+a\s+',
        ]
        for prefix in informal_prefixes:
            text = re.sub(prefix, '', text, flags=re.IGNORECASE)

        # Capitalize first letter and ensure ending period if missing punctuation
        if text:
            text = text[0].upper() + text[1:]
            if not text.endswith(('.', '?', '!')):
                text += '.'

        return text

    def analyze_task(
        self, request: TaskRequest
    ) -> Tuple[TaskOutcome, List[TaskClarification]]:
        """
        Analyzes TaskRequest and returns TaskOutcome and any required TaskClarification list.
        """
        raw_text = request.user_input.strip()
        normalized = self.normalize_request(raw_text)

        clarifications: List[TaskClarification] = []

        # ── 1. Derive Requested Outputs ───────────────────────────────────
        derived_outputs = list(request.requested_outputs)
        text_lower = raw_text.lower()

        for output_type, keywords in KNOWN_OUTPUT_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                if output_type not in derived_outputs:
                    derived_outputs.append(output_type)

        # ── 2. Ambiguity & Under-specification Check ───────────────────────
        if len(raw_text) < 15 or self._is_ambiguous(raw_text, derived_outputs):
            clarifications.append(
                TaskClarification(
                    clarification_id=f"clarify_{uuid.uuid4().hex[:8]}",
                    task_id=request.task_id,
                    question=(
                        "Your request is broad or ambiguous. Which specific deliverable do you need? "
                        "(e.g., promotional video, market research report, landing page, legal review)"
                    ),
                    reason="Request lacks explicit deliverable objective or scope.",
                    required=True,
                    status=ClarificationStatus.PENDING,
                )
            )

        # Fallback default output if none recognized and request is not ambiguous
        if not derived_outputs and not clarifications:
            derived_outputs.append("text_report")

        # ── 3. Success Definition ──────────────────────────────────────────
        success_def = (
            f"A validated output artifact of type(s) [{', '.join(derived_outputs)}] "
            f"exists and satisfies quality requirements."
        )

        outcome = TaskOutcome(
            objective=normalized or raw_text,
            intent=f"Produce requested outputs: {', '.join(derived_outputs)}",
            success_definition=success_def,
            required_outputs=derived_outputs,
            constraints=request.constraints,
        )

        return outcome, clarifications

    def _is_ambiguous(self, text: str, derived_outputs: List[str]) -> bool:
        """Determines whether a user prompt lacks actionable intent or context."""
        if derived_outputs and any(o != "text_report" for o in derived_outputs):
            return False
        lower = text.lower().strip()
        vague_phrases = [
            "make something good",
            "do something",
            "help me with my company",
            "make my startup better",
            "do work",
            "generate something",
            "fix everything",
            "stuff",
            "anything",
        ]
        return any(phrase in lower for phrase in vague_phrases)
