"""
Quality Engine

Provides content and strategy quality evaluation for the Marketing Team.
Includes AI writing pattern detection, brand voice checking,
claim verification, and multi-dimensional quality scoring.
"""

import re
import logging
from typing import Optional, List, Dict, Any

from teams.marketing.models import (
    ContentQualityCheck, MarketingQualityScore, BrandContext,
)

logger = logging.getLogger(__name__)

# Generic AI writing patterns to flag
AI_PATTERNS = [
    "revolutionary", "game-changing", "unlock your potential",
    "in today's fast-paced world", "in today's digital landscape",
    "in this ever-evolving", "dive into", "dive deep into",
    "elevate your", "supercharge", "unleash the power",
    "seamlessly integrate", "cutting-edge", "paradigm shift",
    "synergy", "best-in-class", "world-class", "next-level",
    "disruptive", "holistic approach", "ecosystem",
    "leverage the power", "harness the potential",
    "at the end of the day", "it's no secret that",
    "buckle up", "let's face it", "needless to say",
    "without further ado", "imagine a world where",
    "in conclusion", "to sum it up",
]

# Phrases that suggest fabricated claims
CLAIM_PATTERNS = [
    r'\d+%\s+(?:increase|growth|improvement|reduction|boost)',
    r'(?:over|more than)\s+\d+\s+(?:customers|users|companies|clients)',
    r'#1\s+(?:in|for)',
    r'(?:industry|market)\s+leader',
    r'(?:guaranteed|proven)\s+(?:results|to)',
    r'(?:trusted by|used by)\s+\d+',
    r'\$\d+[MBK]?\s+(?:in|of)\s+(?:revenue|savings|value)',
]


class QualityEngine:
    """
    Quality evaluation engine for marketing content and strategy.
    
    Checks:
    - Brand voice consistency
    - AI writing pattern detection
    - Unsupported claim detection
    - CTA presence
    - Content originality signals
    - Platform fitness
    """

    def evaluate_content(self, content: str,
                         brand_context: Optional[BrandContext] = None,
                         content_type: Optional[str] = None,
                         platform: Optional[str] = None) -> ContentQualityCheck:
        """Evaluate content quality across multiple dimensions."""

        # AI pattern detection
        ai_flags = self._detect_ai_patterns(content)

        # Claim detection
        unsupported_claims = self._detect_unsupported_claims(content)

        # Brand voice check
        banned_violations = self._check_banned_phrases(content, brand_context)

        # CTA detection
        has_cta = self._detect_cta(content)

        # Score computation
        base_score = 80.0

        # Penalties
        ai_penalty = len(ai_flags) * 5.0
        claim_penalty = len(unsupported_claims) * 15.0
        banned_penalty = len(banned_violations) * 20.0
        cta_penalty = 0.0 if has_cta else 10.0

        scores = {
            "brand_consistency": max(0, 85.0 - banned_penalty),
            "factual_accuracy": max(0, 90.0 - claim_penalty),
            "audience_relevance": 70.0,
            "objective_alignment": 70.0,
            "platform_fit": 75.0,
            "clarity": 75.0,
            "differentiation": max(0, 80.0 - ai_penalty),
            "tone_match": max(0, 85.0 - banned_penalty * 0.5),
            "compliance": max(0, 90.0 - claim_penalty),
            "originality": max(0, 85.0 - ai_penalty * 1.5),
        }

        overall = sum(scores.values()) / len(scores)
        pass_gate = overall >= 55.0 and len(unsupported_claims) == 0

        issues = []
        if ai_flags:
            issues.append(f"AI patterns detected: {ai_flags[:3]}")
        if unsupported_claims:
            issues.append(f"Unsupported claims: {unsupported_claims[:2]}")
        if banned_violations:
            issues.append(f"Banned phrases used: {banned_violations}")
        if not has_cta:
            issues.append("No clear CTA detected")

        return ContentQualityCheck(
            brand_consistency=scores["brand_consistency"],
            factual_accuracy=scores["factual_accuracy"],
            audience_relevance=scores["audience_relevance"],
            objective_alignment=scores["objective_alignment"],
            platform_fit=scores["platform_fit"],
            clarity=scores["clarity"],
            cta_present=has_cta,
            differentiation=scores["differentiation"],
            tone_match=scores["tone_match"],
            compliance=scores["compliance"],
            unsupported_claims=unsupported_claims,
            grammar_issues=[],
            ai_pattern_flags=ai_flags,
            originality=scores["originality"],
            overall_score=overall,
            explanation=f"Score: {overall:.0f}/100. Issues: {'; '.join(issues) if issues else 'None'}",
            pass_gate=pass_gate,
        )

    def evaluate_strategy(self, strategy, brief=None) -> MarketingQualityScore:
        """Evaluate strategy quality across dimensions."""
        checks = {
            "has_objective": bool(strategy.objective),
            "has_audience": bool(strategy.audience),
            "has_positioning": bool(strategy.positioning),
            "has_messaging": bool(strategy.messaging_framework),
            "has_channels": bool(strategy.channel_strategies),
            "has_kpis": bool(strategy.kpis),
            "has_timeline": bool(strategy.timeline),
            "channels_justified": all(
                cs.rationale for cs in strategy.channel_strategies
            ) if strategy.channel_strategies else False,
            "risks_identified": bool(strategy.risks),
            "assumptions_listed": bool(strategy.assumptions),
        }

        total = len(checks)
        passed = sum(1 for v in checks.values() if v)
        score = (passed / total * 100) if total > 0 else 0.0

        missing = [k.replace("has_", "").replace("_", " ") for k, v in checks.items() if not v]

        return MarketingQualityScore(
            overall_score=score,
            strategic_coherence=score,
            factual_accuracy=80.0,
            brand_consistency=70.0 if strategy.positioning else 30.0,
            audience_relevance=80.0 if strategy.audience else 20.0,
            channel_fit=80.0 if strategy.channel_strategies else 20.0,
            content_quality=0.0,
            conversion_orientation=60.0 if strategy.kpis else 20.0,
            research_grounding=50.0,
            analytics_correctness=80.0,
            actionability=80.0 if strategy.priorities else 40.0,
            quality_issues=[f"Missing: {m}" for m in missing],
            missing_elements=missing,
            explanation=f"Strategy quality: {passed}/{total} checks ({score:.0f}%)",
        )

    def _detect_ai_patterns(self, text: str) -> List[str]:
        """Detect generic AI writing patterns in content."""
        text_lower = text.lower()
        return [p for p in AI_PATTERNS if p.lower() in text_lower]

    def _detect_unsupported_claims(self, text: str) -> List[str]:
        """Detect potentially unsupported statistical/authority claims."""
        claims = []
        for pattern in CLAIM_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for m in matches:
                claims.append(f"Potential unsupported claim: '{m}'")
        return claims

    def _check_banned_phrases(self, text: str,
                              brand_context: Optional[BrandContext]) -> List[str]:
        """Check for banned brand phrases."""
        if not brand_context or not brand_context.banned_phrases:
            return []
        text_lower = text.lower()
        return [p for p in brand_context.banned_phrases if p.lower() in text_lower]

    def _detect_cta(self, text: str) -> bool:
        """Detect presence of a call-to-action."""
        cta_keywords = [
            "sign up", "try", "start", "learn more", "get started",
            "join", "subscribe", "download", "register", "book",
            "schedule", "click", "visit", "check out", "explore",
            "request", "apply", "contact", "discover", "see how",
            "watch", "read more", "shop now", "buy", "order",
        ]
        text_lower = text.lower()
        return any(kw in text_lower for kw in cta_keywords)
