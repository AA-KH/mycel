"""
Aditya — Fact Checker

Independently verifies claims produced by Aarav.
The critical "Zero-Hallucination" enforcer — designed to make
hallucinations structurally difficult.

Aditya's design principles:
1. Never force certainty — "insufficient evidence" is a valid result
2. Independent verification — searches for claims separately
3. Source comparison — checks multiple independent sources
4. Conflict detection — identifies when sources disagree
5. Temporal awareness — flags potentially outdated information
"""

import asyncio
import json
import re
import logging
from typing import Dict, Any, List, Optional

from core.groq_engine import engine_manager
from teams.research.models import (
    Claim, Source, Evidence, VerificationStatus, ClaimConfidence,
    SourceTier, ResearchTrace
)
from teams.research.engine.search import SearchEngine, SearchResult
from teams.research.engine.fetcher import ContentFetcher
from teams.research.engine.extractor import classify_source, count_independent_sources

logger = logging.getLogger(__name__)

ADITYA_SYSTEM_PROMPT = """You are Aditya, the Fact Checker at Mycel.

Your role is to independently verify claims. You are the last line of defense against misinformation.

You are skeptical, rigorous, and honest. You NEVER manufacture certainty.

RULES:
1. "I don't know" and "insufficient evidence" are VALID answers
2. A claim is VERIFIED only if 2+ independent sources confirm it
3. A claim is DISPUTED if sources conflict — report BOTH sides
4. Marketing claims should be flagged as such, not treated as facts
5. Always check if information might be outdated
6. A single source, no matter how reputable, makes a claim LOW confidence, not VERIFIED
7. Look for disconfirming evidence, not just confirming evidence
8. Report the actual evidence, not what you think should be true"""


class AdityaFactChecker:
    """
    Aditya — Fact Checker Agent
    
    Responsibilities:
    - Independently verify claims from Aarav
    - Search for corroborating AND contradicting evidence
    - Assign verification status (verified/disputed/insufficient/refuted)
    - Detect source conflicts
    - Flag time-sensitive claims
    - Never manufacture certainty
    """
    
    def __init__(self, trace: Optional[ResearchTrace] = None,
                 search_engine: Optional[SearchEngine] = None,
                 fetcher: Optional[ContentFetcher] = None):
        self.name = "Aditya"
        self.role = "Fact Checker"
        self.trace = trace or ResearchTrace()
        # Use SEPARATE search engine and fetcher from Aarav — independent verification
        self.search_engine = search_engine or SearchEngine()
        self.fetcher = fetcher or ContentFetcher()
        self._engine = engine_manager.get_engine("research")
    
    async def verify_claims(self, claims: List[Claim], sources: List[Source],
                             evidence: List[Evidence]) -> List[Claim]:
        """
        Main entry point: verify a batch of claims.
        Returns claims with updated verification status.
        """
        self.trace.log(
            agent=self.name,
            action="started_verification",
            details=f"Verifying {len(claims)} claims"
        )
        
        # Prioritize: verify high-impact claims first
        # Critical/disputed claims get independent verification search
        # Low-priority claims get source-based verification only
        high_priority = [c for c in claims if c.confidence != ClaimConfidence.HIGH or len(c.source_ids) < 2]
        
        # Verify claims — process in parallel batches of 3
        for i in range(0, len(high_priority), 3):
            batch = high_priority[i:i+3]
            tasks = [self._verify_single_claim(c, sources, evidence) for c in batch]
            await asyncio.gather(*tasks)
        
        # For claims already supported by multiple sources, do quick verification
        low_priority = [c for c in claims if c not in high_priority]
        for claim in low_priority:
            self._quick_verify(claim, sources)
        
        # Run cross-claim conflict detection
        self._detect_conflicts(claims)
        
        self.trace.log(
            agent=self.name,
            action="completed_verification",
            details=self._verification_summary(claims)
        )
        
        return claims
    
    async def _verify_single_claim(self, claim: Claim, sources: List[Source],
                                     evidence: List[Evidence]):
        """Verify a single claim through independent search."""
        self.trace.log(
            agent=self.name,
            action="verifying_claim",
            details=f"Checking: {claim.text[:100]}",
            claim_id=claim.claim_id
        )
        
        # Step 1: Check existing source quality
        claim_sources = [s for s in sources if s.source_id in claim.source_ids]
        source_quality = self._assess_source_quality(claim_sources)
        
        # Step 2: If sources are high quality and multiple, quick verify
        independent_count = count_independent_sources(claim_sources)
        if independent_count >= 2 and source_quality >= 2.0:
            claim.verification_status = VerificationStatus.VERIFIED
            claim.confidence = ClaimConfidence.HIGH
            claim.verified_by = self.name
            claim.verification_notes = (
                f"Verified: {independent_count} independent sources confirm. "
                f"Source quality score: {source_quality:.1f}"
            )
            self.trace.log(
                agent=self.name,
                action="claim_verified",
                details=f"Quick-verified via {independent_count} independent sources",
                claim_id=claim.claim_id
            )
            return
        
        # Step 3: Independent verification search
        try:
            verification_result = await self._independent_search_verify(claim)
            
            if verification_result["status"] == "confirmed":
                claim.verification_status = VerificationStatus.VERIFIED
                claim.confidence = ClaimConfidence.HIGH
                claim.verification_notes = verification_result.get("notes", "")
            elif verification_result["status"] == "partially_confirmed":
                claim.verification_status = VerificationStatus.PARTIALLY_VERIFIED
                claim.confidence = ClaimConfidence.MEDIUM
                claim.verification_notes = verification_result.get("notes", "")
            elif verification_result["status"] == "disputed":
                claim.verification_status = VerificationStatus.DISPUTED
                claim.confidence = ClaimConfidence.DISPUTED
                claim.verification_notes = verification_result.get("notes", "")
                claim.conflicts_description = verification_result.get("conflict_details", "")
            elif verification_result["status"] == "refuted":
                claim.verification_status = VerificationStatus.REFUTED
                claim.confidence = ClaimConfidence.LOW
                claim.verification_notes = verification_result.get("notes", "")
            else:
                claim.verification_status = VerificationStatus.INSUFFICIENT_EVIDENCE
                claim.confidence = ClaimConfidence.LOW
                claim.verification_notes = verification_result.get("notes", "Could not find sufficient independent evidence")
            
            claim.verified_by = self.name
            
        except Exception as e:
            logger.error(f"[Aditya] Verification failed for claim {claim.claim_id}: {e}")
            claim.verification_status = VerificationStatus.UNVERIFIED
            claim.verification_notes = f"Verification error: {str(e)[:100]}"
        
        self.trace.log(
            agent=self.name,
            action=f"claim_{claim.verification_status.value}",
            details=f"Status: {claim.verification_status.value}. {claim.verification_notes[:100]}",
            claim_id=claim.claim_id
        )
    
    async def _independent_search_verify(self, claim: Claim) -> Dict[str, Any]:
        """Search independently to verify a claim."""
        # Generate verification queries
        claim_short = claim.text[:80]
        queries = [
            claim_short,
            f"is it true that {claim_short}",
        ]
        
        # Search
        results = await self.search_engine.multi_search(queries, max_results_per_query=3)
        
        if not results:
            return {
                "status": "insufficient",
                "notes": "No independent search results found for verification"
            }
        
        # Fetch top 3 results
        urls = [r.url for r in results[:3] if r.url]
        fetched = await self.fetcher.fetch_multiple(urls)
        
        successful = [f for f in fetched if isinstance(f, type(fetched[0])) and hasattr(f, 'is_success') and f.is_success]
        
        if not successful:
            return {
                "status": "insufficient",
                "notes": "Could not fetch any verification sources"
            }
        
        # Use LLM to check if fetched content supports the claim
        return await self._llm_verify(claim, successful)
    
    async def _llm_verify(self, claim: Claim, fetched_sources) -> Dict[str, Any]:
        """Use LLM to verify a claim against fetched verification sources."""
        source_texts = []
        for i, fetch in enumerate(fetched_sources[:3]):
            content = fetch.content[:2000] if hasattr(fetch, 'content') else ""
            source_texts.append(
                f"[VERIFICATION SOURCE {i+1}] URL: {fetch.url}\n"
                f"Title: {fetch.title if hasattr(fetch, 'title') else ''}\n"
                f"Content:\n{content}\n"
            )
        
        verification_prompt = f"""CLAIM TO VERIFY: "{claim.text}"

VERIFICATION SOURCES:
{chr(10).join(source_texts)}

Analyze whether these independent sources support or contradict the claim.

Return a JSON object:
{{
    "status": "confirmed|partially_confirmed|disputed|refuted|insufficient",
    "notes": "Explanation of your verification decision",
    "conflict_details": "If disputed, describe the conflicting information",
    "supporting_evidence": "Quote from sources that supports the claim",
    "contradicting_evidence": "Quote from sources that contradicts the claim"
}}

RULES:
- "confirmed" = 2+ independent sources clearly support this specific claim
- "partially_confirmed" = sources support the general direction but not exact details
- "disputed" = some sources support, others contradict
- "refuted" = independent evidence directly contradicts the claim
- "insufficient" = cannot determine from available sources
- When in doubt, use "insufficient" — NEVER force certainty"""

        try:
            messages = [
                {"role": "system", "content": ADITYA_SYSTEM_PROMPT},
                {"role": "user", "content": verification_prompt}
            ]
            
            response = await self._engine.chat_completion(
                model="qwen/qwen3.8-27b",
                messages=messages,
                temperature=0.1,
                max_tokens=1500
            )
            
            raw = response.choices[0].message.content or ""
            raw = re.sub(r'<think>.*?</think>', '', raw, flags=re.DOTALL).strip()
            
            json_match = re.search(r'\{.*\}', raw, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                # Validate status
                valid_statuses = {"confirmed", "partially_confirmed", "disputed", "refuted", "insufficient"}
                if result.get("status") not in valid_statuses:
                    result["status"] = "insufficient"
                return result
            
            return {"status": "insufficient", "notes": "Could not parse verification result"}
            
        except Exception as e:
            logger.error(f"[Aditya] LLM verification failed: {e}")
            return {"status": "insufficient", "notes": f"Verification error: {str(e)[:100]}"}
    
    def _quick_verify(self, claim: Claim, sources: List[Source]):
        """Quick verification based on existing source metadata (no new search)."""
        claim_sources = [s for s in sources if s.source_id in claim.source_ids]
        independent = count_independent_sources(claim_sources)
        quality = self._assess_source_quality(claim_sources)
        
        if independent >= 3 and quality >= 2.5:
            claim.verification_status = VerificationStatus.VERIFIED
            claim.confidence = ClaimConfidence.HIGH
        elif independent >= 2 and quality >= 2.0:
            claim.verification_status = VerificationStatus.PARTIALLY_VERIFIED
            claim.confidence = ClaimConfidence.MEDIUM
        elif independent >= 1:
            claim.verification_status = VerificationStatus.PARTIALLY_VERIFIED
            claim.confidence = ClaimConfidence.LOW
        else:
            claim.verification_status = VerificationStatus.INSUFFICIENT_EVIDENCE
            claim.confidence = ClaimConfidence.LOW
        
        claim.verified_by = self.name
        claim.verification_notes = f"Quick-verified: {independent} independent sources, quality={quality:.1f}"
    
    def _assess_source_quality(self, sources: List[Source]) -> float:
        """Compute average source quality score."""
        if not sources:
            return 0.0
        
        tier_scores = {
            SourceTier.PRIMARY: 3.0,
            SourceTier.HIGH_QUALITY_SECONDARY: 2.0,
            SourceTier.COMMUNITY: 1.0,
            SourceTier.LOW_CONFIDENCE: 0.5,
        }
        
        total = sum(tier_scores.get(s.tier, 0.5) for s in sources)
        return total / len(sources)
    
    def _detect_conflicts(self, claims: List[Claim]):
        """Detect potential conflicts between claims."""
        # Group claims by category
        by_category: Dict[str, List[Claim]] = {}
        for claim in claims:
            cat = claim.category or "general"
            by_category.setdefault(cat, []).append(claim)
        
        # Within each category, check for potential conflicts
        # This is a simple heuristic — LLM-based conflict detection would be better
        for category, cat_claims in by_category.items():
            if len(cat_claims) < 2:
                continue
            
            for i, c1 in enumerate(cat_claims):
                for c2 in cat_claims[i+1:]:
                    if self._might_conflict(c1.text, c2.text):
                        c1.conflicting_claim_ids.append(c2.claim_id)
                        c2.conflicting_claim_ids.append(c1.claim_id)
                        
                        self.trace.log(
                            agent=self.name,
                            action="conflict_detected",
                            details=f"Potential conflict: '{c1.text[:50]}' vs '{c2.text[:50]}'",
                            claim_id=c1.claim_id
                        )
    
    def _might_conflict(self, text1: str, text2: str) -> bool:
        """Simple heuristic to detect if two claims might conflict."""
        # Check for negation patterns
        negation_words = {'not', 'no', 'never', 'neither', 'none', "doesn't", "isn't",
                          "wasn't", "aren't", "don't", "won't", "cannot", "can't"}
        
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        # If one has negation and they share significant overlap, might conflict
        has_neg1 = bool(words1 & negation_words)
        has_neg2 = bool(words2 & negation_words)
        
        if has_neg1 != has_neg2:
            # One is negated, the other isn't
            content1 = words1 - negation_words
            content2 = words2 - negation_words
            overlap = len(content1 & content2)
            return overlap >= 3
        
        return False
    
    def _verification_summary(self, claims: List[Claim]) -> str:
        """Generate a summary of verification results."""
        status_counts = {}
        for claim in claims:
            status = claim.verification_status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        parts = [f"{count} {status}" for status, count in sorted(status_counts.items())]
        return f"Verification complete: {', '.join(parts)}"
