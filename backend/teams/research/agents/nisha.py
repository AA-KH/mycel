"""
Nisha — Research Writer

Synthesizes verified claims, evidence, and findings into:
1. A structured ResearchArtifact (for downstream agent consumption)
2. A user-facing research report (human readable)
3. A downstream context object (machine-consumable for other teams)

Nisha NEVER:
- Fills gaps creatively
- Presents unverified claims as verified
- Omits uncertainty or limitations
- Generates new facts not in the evidence
"""

import json
import re
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from core.groq_engine import engine_manager
from teams.research.models import (
    Claim, Source, Evidence, ResearchPlan, ResearchFinding,
    ResearchArtifact, ResearchQualityScore, VerificationStatus,
    ClaimConfidence, ComparisonMatrix, ComparisonEntry,
    DownstreamContext, ResearchTrace, ResearchRequestType
)

logger = logging.getLogger(__name__)

NISHA_SYSTEM_PROMPT = """You are Nisha, the Research Writer at Mycel.

Your role is to synthesize verified research into clear, structured reports.

You are clear, precise, and transparent. You care deeply about accuracy and honesty.

RULES:
1. NEVER add information that isn't in the evidence
2. ALWAYS cite sources for factual claims
3. CLEARLY mark uncertain, disputed, or unverified information
4. Present limitations and gaps honestly
5. Distinguish between verified facts, community opinions, and marketing claims
6. Use structured formatting (headings, bullets, tables)
7. Make the report useful for DECISION-MAKING, not just informational"""


class NishaResearchWriter:
    """
    Nisha — Research Writer Agent
    
    Responsibilities:
    - Synthesize claims into findings
    - Generate quality scores
    - Produce user-facing research report
    - Create downstream context for other teams
    - Build comparison matrices for comparative research
    - Preserve full citation chain
    """
    
    def __init__(self, trace: Optional[ResearchTrace] = None):
        self.name = "Nisha"
        self.role = "Research Writer"
        self.trace = trace or ResearchTrace()
        self._engine = engine_manager.get_engine("research")
    
    async def synthesize(self, plan: ResearchPlan,
                          sources: List[Source],
                          evidence: List[Evidence],
                          claims: List[Claim]) -> ResearchArtifact:
        """
        Main entry point: synthesize all research into a ResearchArtifact.
        """
        self.trace.log(
            agent=self.name,
            action="started_synthesis",
            details=f"Synthesizing {len(claims)} claims from {len(sources)} sources"
        )
        
        # 1. Categorize claims by verification status
        verified_ids = [c.claim_id for c in claims if c.verification_status == VerificationStatus.VERIFIED]
        disputed_ids = [c.claim_id for c in claims if c.verification_status == VerificationStatus.DISPUTED]
        unverified_ids = [c.claim_id for c in claims 
                         if c.verification_status in (VerificationStatus.UNVERIFIED, VerificationStatus.INSUFFICIENT_EVIDENCE)]
        
        # 2. Generate findings (synthesized conclusions)
        findings = await self._generate_findings(plan, claims, sources)
        
        # 3. Build comparison matrix (if comparative research)
        comparison = None
        if plan.research_type in (ResearchRequestType.COMPARATIVE_ANALYSIS,
                                   ResearchRequestType.COMPETITOR_ANALYSIS,
                                   ResearchRequestType.TECHNOLOGY_EVALUATION,
                                   ResearchRequestType.OPEN_SOURCE_EVALUATION):
            comparison = self._build_comparison(plan, claims, sources)
        
        # 4. Calculate quality score
        quality = self._calculate_quality(plan, sources, claims)
        
        # 5. Identify unanswered questions and limitations
        unanswered = [q.text for q in plan.questions if not q.is_answered]
        limitations = self._identify_limitations(plan, sources, claims)
        
        # 6. Generate user-facing report via LLM
        report = await self._generate_report(plan, findings, claims, sources, comparison, quality, limitations)
        
        # 7. Generate executive summary
        executive_summary = await self._generate_executive_summary(plan, findings, quality)
        
        # 8. Build downstream context
        downstream = self._build_downstream_context(plan, findings, claims, limitations)
        
        # 9. Assemble artifact
        artifact = ResearchArtifact(
            original_request=plan.original_request,
            interpreted_objective=plan.interpreted_objective,
            research_type=plan.research_type,
            research_plan=plan,
            sources=sources,
            evidence=evidence,
            claims=claims,
            verified_claims=verified_ids,
            disputed_claims=disputed_ids,
            unverified_claims=unverified_ids,
            findings=findings,
            comparison=comparison,
            unanswered_questions=unanswered,
            limitations=limitations,
            quality_score=quality,
            downstream_context=downstream,
            user_report=report,
            executive_summary=executive_summary,
            trace=self.trace,
            completed_at=datetime.now(timezone.utc),
            total_sources_consulted=len(sources),
        )
        
        self.trace.log(
            agent=self.name,
            action="completed_synthesis",
            details=f"Artifact complete. Quality: {quality.overall_score:.0f}/100. "
                    f"Verified: {len(verified_ids)}, Disputed: {len(disputed_ids)}, Unverified: {len(unverified_ids)}"
        )
        
        return artifact
    
    async def _generate_findings(self, plan: ResearchPlan, claims: List[Claim],
                                   sources: List[Source]) -> List[ResearchFinding]:
        """Group and synthesize claims into research findings."""
        # Group claims by category
        by_category: Dict[str, List[Claim]] = {}
        for claim in claims:
            cat = claim.category or "general"
            by_category.setdefault(cat, []).append(claim)
        
        findings = []
        for category, cat_claims in by_category.items():
            # Only create findings for categories with verified or partially verified claims
            meaningful_claims = [c for c in cat_claims 
                                if c.verification_status in (VerificationStatus.VERIFIED, 
                                                              VerificationStatus.PARTIALLY_VERIFIED)]
            
            if not meaningful_claims:
                # Even disputed or unverified claims form a finding, just with low confidence
                meaningful_claims = cat_claims
            
            if not meaningful_claims:
                continue
            
            # Determine confidence for the finding
            if any(c.verification_status == VerificationStatus.VERIFIED for c in meaningful_claims):
                confidence = ClaimConfidence.HIGH
            elif any(c.verification_status == VerificationStatus.PARTIALLY_VERIFIED for c in meaningful_claims):
                confidence = ClaimConfidence.MEDIUM
            else:
                confidence = ClaimConfidence.LOW
            
            # Create summary from claims
            claim_texts = [c.text for c in meaningful_claims[:5]]
            summary = " | ".join(claim_texts)
            
            finding = ResearchFinding(
                title=f"{category.replace('_', ' ').title()} Findings",
                summary=summary[:500],
                claim_ids=[c.claim_id for c in meaningful_claims],
                confidence=confidence,
                category=category
            )
            findings.append(finding)
            
            self.trace.log(
                agent=self.name,
                action="created_finding",
                details=f"Finding: {finding.title} ({len(meaningful_claims)} claims, {confidence.value})"
            )
        
        return findings
    
    def _build_comparison(self, plan: ResearchPlan, claims: List[Claim],
                           sources: List[Source]) -> Optional[ComparisonMatrix]:
        """Build a comparison matrix from claims about multiple entities."""
        entities = plan.key_entities
        if len(entities) < 2:
            return None
        
        # Common comparison criteria
        criteria = set()
        entries = []
        
        for claim in claims:
            if claim.verification_status in (VerificationStatus.REFUTED,):
                continue
            
            # Try to match claim to an entity
            claim_lower = claim.text.lower()
            for entity in entities:
                if entity.lower() in claim_lower:
                    # This claim is about this entity
                    category = claim.category or "general"
                    criteria.add(category)
                    
                    entries.append(ComparisonEntry(
                        entity=entity,
                        criterion=category,
                        value=claim.text[:200],
                        source_ids=claim.source_ids,
                        confidence=claim.confidence
                    ))
                    break
        
        if not entries:
            return None
        
        return ComparisonMatrix(
            entities=entities,
            criteria=sorted(list(criteria)),
            entries=entries
        )
    
    def _calculate_quality(self, plan: ResearchPlan, sources: List[Source],
                            claims: List[Claim]) -> ResearchQualityScore:
        """Calculate an explainable quality score."""
        total_questions = len(plan.questions)
        answered_questions = sum(1 for q in plan.questions if q.is_answered)
        
        # Question coverage
        question_coverage = (answered_questions / total_questions * 100) if total_questions > 0 else 0
        
        # Source quality
        tier_scores = {
            "primary": 3.0, "secondary": 2.0, "community": 1.0, "low_confidence": 0.5
        }
        accessible_sources = [s for s in sources if s.is_accessible]
        source_quality = 0.0
        if accessible_sources:
            source_quality = sum(tier_scores.get(s.tier.value, 0.5) for s in accessible_sources) / len(accessible_sources)
            source_quality = source_quality / 3.0 * 100  # Normalize to 0-100
        
        # Source diversity
        source_types = set(s.source_type.value for s in accessible_sources)
        source_diversity = min(len(source_types) / 5 * 100, 100)  # 5 types = 100%
        
        # Evidence density
        evidence_density = min(len(claims) / max(total_questions, 1) * 20, 100)
        
        # Verification coverage
        verified = sum(1 for c in claims if c.verification_status in 
                       (VerificationStatus.VERIFIED, VerificationStatus.PARTIALLY_VERIFIED))
        verification_coverage = (verified / max(len(claims), 1)) * 100
        
        # Recency
        recency = 50.0  # Default
        
        # Contradictions
        contradictions = sum(1 for c in claims if c.conflicting_claim_ids)
        
        # Overall score (weighted average)
        overall = (
            question_coverage * 0.25 +
            source_quality * 0.20 +
            source_diversity * 0.10 +
            evidence_density * 0.15 +
            verification_coverage * 0.25 +
            recency * 0.05
        )
        
        # Penalty for contradictions
        overall = max(0, overall - contradictions * 5)
        
        explanation_parts = []
        if question_coverage < 50:
            explanation_parts.append(f"Low question coverage ({question_coverage:.0f}%)")
        if verification_coverage < 50:
            explanation_parts.append(f"Many claims unverified ({verification_coverage:.0f}% verified)")
        if contradictions > 0:
            explanation_parts.append(f"{contradictions} conflicting claims detected")
        if source_diversity < 40:
            explanation_parts.append("Limited source diversity")
        if not explanation_parts:
            explanation_parts.append("Good coverage, verification, and source diversity")
        
        return ResearchQualityScore(
            overall_score=round(min(overall, 100), 1),
            question_coverage_pct=round(question_coverage, 1),
            source_quality_avg=round(source_quality, 1),
            source_diversity_score=round(source_diversity, 1),
            evidence_density=round(evidence_density, 1),
            verification_coverage_pct=round(verification_coverage, 1),
            recency_score=recency,
            contradiction_count=contradictions,
            unresolved_questions=total_questions - answered_questions,
            explanation="; ".join(explanation_parts)
        )
    
    def _identify_limitations(self, plan: ResearchPlan, sources: List[Source],
                               claims: List[Claim]) -> List[str]:
        """Identify research limitations honestly."""
        limitations = []
        
        # Source access failures
        failed_sources = [s for s in sources if not s.is_accessible]
        if failed_sources:
            limitations.append(f"{len(failed_sources)} sources could not be accessed")
        
        # Unanswered questions
        unanswered = [q for q in plan.questions if not q.is_answered]
        if unanswered:
            limitations.append(f"{len(unanswered)} research questions remain unanswered")
        
        # Low source diversity
        source_types = set(s.source_type.value for s in sources if s.is_accessible)
        if len(source_types) < 3:
            limitations.append("Limited diversity of source types")
        
        # Disputed claims
        disputed = [c for c in claims if c.verification_status == VerificationStatus.DISPUTED]
        if disputed:
            limitations.append(f"{len(disputed)} claims have conflicting information across sources")
        
        # Single-source claims
        single_source = [c for c in claims if len(c.source_ids) < 2]
        if len(single_source) > len(claims) / 2:
            limitations.append("Many claims based on a single source")
        
        # Geographic/language bias
        limitations.append("Research primarily covers English-language sources")
        
        return limitations
    
    async def _generate_report(self, plan: ResearchPlan, findings: List[ResearchFinding],
                                 claims: List[Claim], sources: List[Source],
                                 comparison: Optional[ComparisonMatrix],
                                 quality: ResearchQualityScore,
                                 limitations: List[str]) -> str:
        """Generate user-facing research report using LLM."""
        
        # Build input for the LLM
        findings_text = ""
        for f in findings:
            findings_text += f"\n### {f.title}\n"
            findings_text += f"Confidence: {f.confidence.value}\n"
            # Get claims for this finding
            finding_claims = [c for c in claims if c.claim_id in f.claim_ids]
            for c in finding_claims[:5]:
                status_emoji = {
                    VerificationStatus.VERIFIED: "✅",
                    VerificationStatus.PARTIALLY_VERIFIED: "🔶",
                    VerificationStatus.DISPUTED: "⚠️",
                    VerificationStatus.REFUTED: "❌",
                    VerificationStatus.INSUFFICIENT_EVIDENCE: "❓",
                    VerificationStatus.UNVERIFIED: "❓",
                }
                emoji = status_emoji.get(c.verification_status, "❓")
                findings_text += f"- {emoji} {c.text}\n"
        
        # Source citations
        source_citations = ""
        for i, s in enumerate(sources[:15]):
            if s.is_accessible:
                source_citations += f"[{i+1}] {s.title or s.url} — {s.url} (Tier: {s.tier.value})\n"
        
        # Comparison table
        comparison_text = ""
        if comparison and comparison.entries:
            comparison_text = "\n### Comparison Matrix\n"
            for entity in comparison.entities:
                comparison_text += f"\n**{entity}**:\n"
                entity_entries = [e for e in comparison.entries if e.entity == entity]
                for entry in entity_entries:
                    comparison_text += f"- {entry.criterion}: {entry.value[:100]}\n"
        
        report_prompt = f"""Write a professional research report based on these verified findings.

RESEARCH OBJECTIVE: {plan.interpreted_objective}

FINDINGS:
{findings_text}

{comparison_text}

QUALITY SCORE: {quality.overall_score:.0f}/100
- Questions answered: {quality.question_coverage_pct:.0f}%
- Claims verified: {quality.verification_coverage_pct:.0f}%

LIMITATIONS:
{chr(10).join(f'- {l}' for l in limitations)}

SOURCE CITATIONS:
{source_citations}

Write a structured research report with:
1. Executive Summary (2-3 sentences)
2. Key Findings (organized by topic)
3. Detailed Analysis
4. Comparison Table (if applicable)
5. Limitations & Uncertainties
6. Sources

RULES:
- Cite sources using [N] notation
- Clearly mark disputed or unverified information with ⚠️
- DO NOT add any information not in the findings above
- Use markdown formatting"""

        try:
            messages = [
                {"role": "system", "content": NISHA_SYSTEM_PROMPT},
                {"role": "user", "content": report_prompt}
            ]
            
            response = await self._engine.chat_completion(
                model="qwen/qwen3.8-27b",
                messages=messages,
                temperature=0.3,
                max_tokens=4000
            )
            
            raw = response.choices[0].message.content or ""
            raw = re.sub(r'<think>.*?</think>', '', raw, flags=re.DOTALL).strip()
            return raw
            
        except Exception as e:
            logger.error(f"[Nisha] Report generation failed: {e}")
            # Fallback: structured plaintext
            return self._fallback_report(plan, findings, claims, sources, limitations, quality)
    
    async def _generate_executive_summary(self, plan: ResearchPlan,
                                            findings: List[ResearchFinding],
                                            quality: ResearchQualityScore) -> str:
        """Generate a 2-3 sentence executive summary."""
        findings_overview = "; ".join(f.title for f in findings[:5])
        
        prompt = f"""Write a 2-3 sentence executive summary for this research.
Objective: {plan.interpreted_objective}
Key topics: {findings_overview}
Quality: {quality.overall_score:.0f}/100
Limitations: {quality.explanation}

Be concise, factual, and specific. Don't use filler words."""

        try:
            messages = [
                {"role": "system", "content": "You write concise executive summaries. 2-3 sentences maximum."},
                {"role": "user", "content": prompt}
            ]
            
            response = await self._engine.chat_completion(
                model="qwen/qwen3.8-27b",
                messages=messages,
                temperature=0.2,
                max_tokens=300
            )
            
            raw = response.choices[0].message.content or ""
            return re.sub(r'<think>.*?</think>', '', raw, flags=re.DOTALL).strip()
            
        except Exception:
            return f"Research completed on: {plan.interpreted_objective}. Quality: {quality.overall_score:.0f}/100."
    
    def _build_downstream_context(self, plan: ResearchPlan, findings: List[ResearchFinding],
                                    claims: List[Claim], limitations: List[str]) -> DownstreamContext:
        """Build machine-consumable context for other teams."""
        # Extract key facts from verified claims
        key_facts = [c.text for c in claims 
                     if c.verification_status in (VerificationStatus.VERIFIED, VerificationStatus.PARTIALLY_VERIFIED)][:20]
        
        # Extract risks from disputed claims
        risks = [f"DISPUTED: {c.text}" for c in claims 
                 if c.verification_status == VerificationStatus.DISPUTED]
        
        # Technical findings
        technical = [c.text for c in claims if c.category in ("technical", "features", "infrastructure")][:10]
        
        # Market conditions
        market = [c.text for c in claims if c.category in ("market", "pricing", "competitive", "trend")][:10]
        
        # Open questions
        open_questions = [q.text for q in plan.questions if not q.is_answered]
        
        return DownstreamContext(
            objective=plan.interpreted_objective,
            key_facts=key_facts,
            important_entities=plan.key_entities,
            constraints=limitations,
            market_conditions=market,
            technical_findings=technical,
            open_questions=open_questions,
            risks=risks,
            recommended_next_actions=[
                f"Investigate: {q}" for q in open_questions[:3]
            ]
        )
    
    def _fallback_report(self, plan: ResearchPlan, findings: List[ResearchFinding],
                          claims: List[Claim], sources: List[Source],
                          limitations: List[str], quality: ResearchQualityScore) -> str:
        """Generate a structured plaintext report when LLM fails."""
        lines = [
            f"# Research Report: {plan.interpreted_objective}",
            f"\n**Quality Score**: {quality.overall_score:.0f}/100",
            f"\n## Key Findings\n",
        ]
        
        for finding in findings:
            lines.append(f"### {finding.title}")
            finding_claims = [c for c in claims if c.claim_id in finding.claim_ids]
            for c in finding_claims[:5]:
                lines.append(f"- [{c.verification_status.value}] {c.text}")
            lines.append("")
        
        lines.append("\n## Limitations\n")
        for lim in limitations:
            lines.append(f"- {lim}")
        
        lines.append("\n## Sources\n")
        for i, s in enumerate(sources[:15]):
            if s.is_accessible:
                lines.append(f"[{i+1}] {s.title or s.url} — {s.url}")
        
        return "\n".join(lines)
