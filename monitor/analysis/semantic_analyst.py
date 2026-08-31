"""
Semantic analyst — on-demand service, NOT an agent.

Stateless analysis service invoked selectively. Called ONLY when the
deterministic pipeline produces a result that needs semantic judgment:
- "Does this article actually describe a production shutdown at Supplier A?"
- "When it says 'operations suspended,' does that refer to manufacturing?"
- "Are these three reports about the same incident?"
- Generate human-readable "why it matters" summary

NEVER called for:
- "Is Supplier A important?" (network data)
- Geographic distance (Haversine)
- Entity matching (deterministic)
- Deduplication (hashing)

Receives pre-correlated situation context from the correlation engine.
"""

from __future__ import annotations

import json
from typing import Optional

from loguru import logger

from ..models.events import CanonicalEvent
from ..models.situations import RelevanceBreakdown, Situation
from .llm_client import LLMClient


# System prompt — narrowly scoped
SYSTEM_PROMPT = """You are a supply-chain intelligence analyst. You analyze news articles and event reports to determine their ACTUAL impact on a specific supply network.

Your job is strictly limited to semantic interpretation:
1. Does this report ACTUALLY describe the claimed disruption? (not just a mention)
2. Does the disruption actually affect the specific entity, or is it a different entity with a similar name?
3. What is the concrete operational impact?
4. Generate a brief "why it matters" explanation.

Rules:
- Do NOT assess importance — the network model already knows criticality and dependency.
- Do NOT assess geography — spatial matching is already done.
- Do NOT fabricate information — only interpret what the text actually says.
- Be concise. Max 3 sentences per field.
- If uncertain, say so explicitly.

Respond ONLY in valid JSON with these fields:
{
  "confirms_disruption": true/false,
  "confidence": 0.0-1.0,
  "actual_impact": "string describing what actually happened",
  "entity_confirmed": true/false,
  "disambiguation_note": "string if entity confusion possible, null otherwise",
  "why_it_matters": "string explaining operational significance",
  "is_ongoing": true/false
}"""


class SemanticAnalyst:
    """On-demand semantic analysis service.

    Stateless. Each call is independent. No agent lifecycle.
    No autonomous loops. Simple failure handling.
    """

    def __init__(self, llm: LLMClient):
        self.llm = llm

    @property
    def is_available(self) -> bool:
        return self.llm.is_available

    async def analyze_event(
        self,
        event: CanonicalEvent,
        relevance: RelevanceBreakdown,
        situation: Optional[Situation] = None,
    ) -> Optional[AnalysisResult]:
        """Analyze a single event for semantic content.

        Called when the deterministic pipeline needs semantic judgment.
        Returns structured analysis, or None on failure (graceful degradation).
        """
        if not self.is_available:
            event.log("SEMANTIC: LLM not available — using deterministic result")
            return None

        # Build context for the LLM
        user_prompt = self._build_prompt(event, relevance, situation)

        try:
            response = await self.llm.complete(SYSTEM_PROMPT, user_prompt)
            if not response:
                event.log("SEMANTIC: LLM returned empty response")
                return None

            result = self._parse_response(response)
            if result:
                event.log(f"SEMANTIC: confirms_disruption={result.confirms_disruption}, confidence={result.confidence:.2f}")
            return result

        except Exception as e:
            logger.warning(f"Semantic analysis failed: {e}")
            event.log(f"SEMANTIC: analysis failed — {e}")
            return None

    async def analyze_situation(
        self,
        situation: Situation,
        events: list[CanonicalEvent],
    ) -> Optional[str]:
        """Generate a "why it matters" summary for a correlated situation.

        Called after correlation groups events together. The LLM receives
        pre-correlated context: "Three sources describe potentially related
        disruption around Supplier A."
        """
        if not self.is_available:
            return None

        prompt = self._build_situation_prompt(situation, events)

        try:
            response = await self.llm.complete(SYSTEM_PROMPT, prompt)
            return response
        except Exception as e:
            logger.warning(f"Situation analysis failed: {e}")
            return None

    def _build_prompt(
        self,
        event: CanonicalEvent,
        relevance: RelevanceBreakdown,
        situation: Optional[Situation],
    ) -> str:
        """Build a focused prompt for event analysis."""
        parts = [
            f"ARTICLE TITLE: {event.title}",
        ]

        if event.description and event.description != event.title:
            # Truncate description to save tokens
            desc = event.description[:500]
            parts.append(f"ARTICLE TEXT: {desc}")

        parts.append(f"SOURCE: {event.source}")

        if relevance.entity_name:
            parts.append(f"MATCHED ENTITY: {relevance.entity_name}")
            parts.append(f"ENTITY DEPENDENCY SHARE: {relevance.dependency_share:.0%}")
            parts.append(f"ENTITY CRITICALITY: {relevance.criticality:.2f}")

        if relevance.location_name:
            parts.append(f"MATCHED LOCATION: {relevance.location_name}")
            if relevance.location_distance_km is not None:
                parts.append(f"DISTANCE: {relevance.location_distance_km:.1f} km")

        if situation:
            parts.append(f"SITUATION: {len(situation.event_ids)} related events detected")
            parts.append(f"INDEPENDENT SOURCES: {situation.independent_source_count}")

        parts.append("\nQUESTION: Does this article describe an actual disruption affecting the matched entity? Respond in JSON only.")

        return "\n".join(parts)

    def _build_situation_prompt(
        self,
        situation: Situation,
        events: list[CanonicalEvent],
    ) -> str:
        """Build a prompt for situation-level analysis."""
        parts = [
            f"SITUATION: {situation.title}",
            f"NUMBER OF EVENTS: {len(events)}",
            f"INDEPENDENT SOURCES: {situation.independent_source_count}",
            f"AFFECTED ENTITIES: {', '.join(situation.affected_entity_ids)}",
            "",
            "EVENT TITLES:",
        ]

        for i, event in enumerate(events[:5], 1):  # Cap at 5 to save tokens
            parts.append(f"{i}. [{event.source}] {event.title}")

        parts.append("")
        parts.append("Generate a brief 'why it matters' explanation for the supply network. JSON only.")

        return "\n".join(parts)

    def _parse_response(self, response: str) -> Optional[AnalysisResult]:
        """Parse LLM JSON response into structured result."""
        try:
            # Clean up response (strip markdown code fences)
            cleaned = response.strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                cleaned = "\n".join(lines[1:-1]) if len(lines) > 2 else cleaned

            data = json.loads(cleaned)
            return AnalysisResult(
                confirms_disruption=data.get("confirms_disruption", False),
                confidence=float(data.get("confidence", 0.5)),
                actual_impact=data.get("actual_impact", ""),
                entity_confirmed=data.get("entity_confirmed", True),
                disambiguation_note=data.get("disambiguation_note"),
                why_it_matters=data.get("why_it_matters", ""),
                is_ongoing=data.get("is_ongoing", True),
            )
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.debug(f"Failed to parse LLM response: {e}")
            return None


class AnalysisResult:
    """Structured result from semantic analysis."""

    __slots__ = (
        "confirms_disruption", "confidence", "actual_impact",
        "entity_confirmed", "disambiguation_note", "why_it_matters",
        "is_ongoing",
    )

    def __init__(
        self,
        confirms_disruption: bool,
        confidence: float,
        actual_impact: str,
        entity_confirmed: bool,
        disambiguation_note: Optional[str],
        why_it_matters: str,
        is_ongoing: bool,
    ):
        self.confirms_disruption = confirms_disruption
        self.confidence = confidence
        self.actual_impact = actual_impact
        self.entity_confirmed = entity_confirmed
        self.disambiguation_note = disambiguation_note
        self.why_it_matters = why_it_matters
        self.is_ongoing = is_ongoing
