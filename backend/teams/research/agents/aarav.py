"""
Aarav — Researcher

Actually investigates the research questions through iterative web research.
Does NOT simply search once and summarize — performs iterative investigation:

SEARCH → inspect results → identify gaps → refine queries → 
investigate sources → compare → collect evidence → stop when sufficient.

Aarav is meticulous and evidence-focused. Every claim must have a source.
"""

import asyncio
import json
import re
import logging
from typing import Dict, Any, List, Optional, Set

from core.groq_engine import engine_manager
from teams.research.models import (
    ResearchQuestion, ResearchPlan, Source, Evidence, Claim,
    SourceTier, SourceType, ClaimConfidence, VerificationStatus,
    ResearchTrace, SearchStrategy
)
from teams.research.engine.search import SearchEngine, SearchResult
from teams.research.engine.fetcher import ContentFetcher, FetchResult
from teams.research.engine.extractor import (
    classify_source, create_source_from_fetch,
    extract_evidence_snippets, extract_pricing, count_independent_sources
)

logger = logging.getLogger(__name__)

AARAV_SYSTEM_PROMPT = """You are Aarav, the Researcher at Mycel.

Your role is to investigate research questions and extract factual claims with evidence.

You are meticulous, evidence-driven, and objective. You NEVER fabricate information.

RULES:
1. Every claim MUST be based on evidence you actually found
2. If you cannot find information, say so explicitly
3. Distinguish between facts, opinions, and company marketing claims
4. Note the source quality (official docs vs blog posts vs forums)
5. Flag when information might be outdated
6. When sources conflict, report BOTH sides
7. NEVER invent URLs, statistics, quotes, or citations
8. Prefer primary sources over secondary ones

You analyze text content and extract structured findings."""


class AaravResearcher:
    """
    Aarav — Researcher Agent
    
    Responsibilities:
    - Execute search queries for research questions
    - Fetch and analyze web pages
    - Extract evidence and claims
    - Identify information gaps
    - Perform iterative search refinement
    - Track source provenance
    """
    
    def __init__(self, trace: Optional[ResearchTrace] = None,
                 search_engine: Optional[SearchEngine] = None,
                 fetcher: Optional[ContentFetcher] = None):
        self.name = "Aarav"
        self.role = "Researcher"
        self.trace = trace or ResearchTrace()
        self.search_engine = search_engine or SearchEngine()
        self.fetcher = fetcher or ContentFetcher()
        self._engine = engine_manager.get_engine("research")
        
        # Collection state
        self.sources: List[Source] = []
        self.evidence: List[Evidence] = []
        self.claims: List[Claim] = []
        
        # Tracking
        self._investigated_urls: Set[str] = set()
    
    async def investigate_plan(self, plan: ResearchPlan) -> Dict[str, Any]:
        """
        Main entry point: investigate all questions in a research plan.
        Returns collected sources, evidence, and claims.
        """
        self.trace.log(
            agent=self.name,
            action="started_investigation",
            details=f"Investigating {len(plan.questions)} research questions"
        )
        
        # Sort questions by priority (critical first), respecting dependencies
        ordered_questions = self._order_questions(plan.questions)
        
        for question in ordered_questions:
            await self._investigate_question(question, plan)
        
        self.trace.log(
            agent=self.name,
            action="completed_investigation",
            details=f"Collected {len(self.sources)} sources, {len(self.evidence)} evidence items, {len(self.claims)} claims"
        )
        
        return {
            "sources": self.sources,
            "evidence": self.evidence,
            "claims": self.claims,
            "total_searches": self.search_engine.total_searches,
            "total_unique_results": self.search_engine.total_unique_results,
        }
    
    async def _investigate_question(self, question: ResearchQuestion, plan: ResearchPlan):
        """Investigate a single research question through iterative search."""
        self.trace.log(
            agent=self.name,
            action="investigating_question",
            details=f"Q: {question.text[:150]}",
            question_id=question.question_id
        )
        
        # Phase 1: Execute initial search queries
        search_results = await self._execute_searches(question)
        
        if not search_results:
            self.trace.log(
                agent=self.name,
                action="no_search_results",
                details=f"No results found for question: {question.text[:100]}",
                question_id=question.question_id
            )
            return
        
        # Phase 2: Fetch and analyze top sources
        fetched = await self._fetch_top_sources(search_results, question)
        
        # Phase 3: Extract claims from fetched content using LLM
        question_claims = await self._extract_claims_llm(fetched, question, plan)
        
        # Phase 4: Check if we have sufficient coverage
        if len(question_claims) < 2 and question.priority.value in ("critical", "high"):
            # Insufficient — try additional searches
            self.trace.log(
                agent=self.name,
                action="insufficient_evidence",
                details=f"Only {len(question_claims)} claims found. Performing additional searches.",
                question_id=question.question_id
            )
            additional_results = await self._refine_search(question, search_results)
            if additional_results:
                additional_fetched = await self._fetch_top_sources(additional_results, question)
                additional_claims = await self._extract_claims_llm(additional_fetched, question, plan)
                question_claims.extend(additional_claims)
        
        # Update question status
        if question_claims:
            question.is_answered = True
            question.claim_ids = [c.claim_id for c in question_claims]
            question.answer_summary = f"Found {len(question_claims)} claims from {len(set(c.source_ids[0] for c in question_claims if c.source_ids))} sources"
    
    async def _execute_searches(self, question: ResearchQuestion) -> List[SearchResult]:
        """Execute all search queries for a question."""
        queries = question.search_strategy.queries
        if not queries:
            # Generate basic queries from the question text
            queries = [question.text, f"{question.text} 2026"]
        
        all_results = await self.search_engine.multi_search(queries, max_results_per_query=5)
        
        for query in queries:
            self.trace.log(
                agent=self.name,
                action="executed_search",
                details=f"Search: '{query}' → {len(all_results)} total results",
                question_id=question.question_id,
                tool_used="web.search"
            )
        
        return all_results
    
    async def _fetch_top_sources(self, search_results: List[SearchResult],
                                   question: ResearchQuestion) -> List[FetchResult]:
        """Fetch and extract content from the most promising search results."""
        # Prioritize results by source quality
        ranked = self._rank_results(search_results, question)
        
        # Fetch top N (don't fetch everything — be efficient)
        max_fetch = min(6, len(ranked))
        urls_to_fetch = []
        for result in ranked[:max_fetch]:
            if result.url and result.url not in self._investigated_urls:
                urls_to_fetch.append(result.url)
                self._investigated_urls.add(result.url)
        
        if not urls_to_fetch:
            return []
        
        fetched = await self.fetcher.fetch_multiple(urls_to_fetch)
        
        # Create Source objects for successful fetches
        successful = []
        for fetch_result in fetched:
            if isinstance(fetch_result, FetchResult) and fetch_result.is_success:
                source = create_source_from_fetch(
                    url=fetch_result.url,
                    title=fetch_result.title,
                    author=fetch_result.author,
                    published_date=fetch_result.published_date,
                    description=fetch_result.description,
                    content_hash=fetch_result.content_hash,
                    is_accessible=True
                )
                self.sources.append(source)
                successful.append(fetch_result)
                
                self.trace.log(
                    agent=self.name,
                    action="fetched_source",
                    details=f"Fetched: {fetch_result.title[:80]} ({len(fetch_result.content)} chars)",
                    source_id=source.source_id,
                    question_id=question.question_id,
                    tool_used="browser.open"
                )
            elif isinstance(fetch_result, FetchResult):
                # Record failed fetch
                source = create_source_from_fetch(
                    url=fetch_result.url,
                    is_accessible=False,
                    access_error=fetch_result.error
                )
                self.sources.append(source)
                
                self.trace.log(
                    agent=self.name,
                    action="fetch_failed",
                    details=f"Failed to fetch {fetch_result.url}: {fetch_result.error}",
                    source_id=source.source_id,
                    question_id=question.question_id
                )
        
        return successful
    
    async def _extract_claims_llm(self, fetched: List[FetchResult], 
                                    question: ResearchQuestion,
                                    plan: ResearchPlan) -> List[Claim]:
        """Use LLM to extract structured claims from fetched content."""
        if not fetched:
            return []
        
        # Build context from all fetched sources
        source_texts = []
        source_map = {}  # index → source_id
        
        for i, fetch_result in enumerate(fetched):
            # Find matching source
            matching_source = next(
                (s for s in self.sources if s.url == fetch_result.url and s.is_accessible),
                None
            )
            if not matching_source:
                continue
            
            # Truncate content for LLM context
            content_preview = fetch_result.content[:3000]
            source_texts.append(
                f"[SOURCE {i+1}] URL: {fetch_result.url}\n"
                f"Title: {fetch_result.title}\n"
                f"Content:\n{content_preview}\n"
            )
            source_map[str(i+1)] = matching_source.source_id
        
        if not source_texts:
            return []
        
        # Ask LLM to extract claims
        extraction_prompt = f"""RESEARCH QUESTION: {question.text}

OVERALL OBJECTIVE: {plan.interpreted_objective}

SOURCES:
{chr(10).join(source_texts[:4])}

Extract specific factual claims that answer the research question.

Return a JSON array of claims:
[
    {{
        "claim": "Specific factual assertion",
        "source_numbers": [1, 2],
        "category": "{question.category or 'general'}",
        "is_time_sensitive": true/false,
        "evidence_quote": "Direct quote or paraphrase from source"
    }}
]

RULES:
- Each claim must be a specific, verifiable assertion
- Include source numbers for traceability
- Do NOT invent claims — only extract what the sources actually say
- If sources disagree, create separate claims noting the conflict
- Distinguish company marketing claims from independent observations
- If you cannot find relevant information in these sources, return an empty array []"""

        try:
            messages = [
                {"role": "system", "content": AARAV_SYSTEM_PROMPT},
                {"role": "user", "content": extraction_prompt}
            ]
            
            response = await self._engine.chat_completion(
                model="qwen/qwen3.8-27b",
                messages=messages,
                temperature=0.2,
                max_tokens=3000
            )
            
            raw = response.choices[0].message.content or ""
            raw = re.sub(r'<think>.*?</think>', '', raw, flags=re.DOTALL).strip()
            
            # Extract JSON array
            json_match = re.search(r'\[.*\]', raw, re.DOTALL)
            if not json_match:
                return []
            
            claims_data = json.loads(json_match.group())
            
            extracted_claims = []
            for c_data in claims_data:
                claim_text = c_data.get("claim", "").strip()
                if not claim_text:
                    continue
                
                # Map source numbers to source IDs
                source_nums = c_data.get("source_numbers", [])
                source_ids = [source_map[str(n)] for n in source_nums if str(n) in source_map]
                
                # Create evidence object
                evidence_text = c_data.get("evidence_quote", claim_text)
                if source_ids:
                    ev = Evidence(
                        source_id=source_ids[0],
                        text=evidence_text[:1000],
                        extracted_by=self.name,
                        relevance_score=0.8
                    )
                    self.evidence.append(ev)
                    evidence_ids = [ev.evidence_id]
                else:
                    evidence_ids = []
                
                claim = Claim(
                    text=claim_text,
                    evidence_ids=evidence_ids,
                    source_ids=source_ids,
                    confidence=ClaimConfidence.MEDIUM if len(source_ids) >= 2 else ClaimConfidence.LOW,
                    category=c_data.get("category", question.category or "general"),
                    is_time_sensitive=c_data.get("is_time_sensitive", False),
                )
                
                self.claims.append(claim)
                extracted_claims.append(claim)
                
                self.trace.log(
                    agent=self.name,
                    action="extracted_claim",
                    details=f"Claim: {claim_text[:100]}",
                    claim_id=claim.claim_id,
                    question_id=question.question_id,
                    source_id=source_ids[0] if source_ids else None
                )
            
            return extracted_claims
            
        except Exception as e:
            logger.error(f"[Aarav] Claim extraction failed: {e}")
            return []
    
    async def _refine_search(self, question: ResearchQuestion,
                               existing_results: List[SearchResult]) -> List[SearchResult]:
        """Generate refined search queries when initial results are insufficient."""
        existing_domains = set(r.domain for r in existing_results)
        
        # Generate alternative queries
        refined_queries = [
            f"{question.text} detailed",
            f"{question.text} site:reddit.com",
            f'"{question.text[:50]}"',  # Exact match
        ]
        
        # Add year for currency
        if question.requires_current_info:
            refined_queries.append(f"{question.text} 2026")
        
        results = await self.search_engine.multi_search(refined_queries, max_results_per_query=3)
        
        # Filter to new domains only
        new_results = [r for r in results if r.domain not in existing_domains]
        
        self.trace.log(
            agent=self.name,
            action="refined_search",
            details=f"Refined search produced {len(new_results)} new results",
            question_id=question.question_id
        )
        
        return new_results
    
    def _rank_results(self, results: List[SearchResult], 
                       question: ResearchQuestion) -> List[SearchResult]:
        """Rank search results by estimated quality and relevance."""
        def score(result: SearchResult) -> float:
            s = 0.0
            
            # Source tier scoring
            _, tier = classify_source(result.url, result.title)
            tier_scores = {
                SourceTier.PRIMARY: 3.0,
                SourceTier.HIGH_QUALITY_SECONDARY: 2.0,
                SourceTier.COMMUNITY: 1.0,
                SourceTier.LOW_CONFIDENCE: 0.5,
            }
            s += tier_scores.get(tier, 0.5)
            
            # Snippet relevance
            question_words = set(question.text.lower().split())
            snippet_words = set(result.snippet.lower().split())
            overlap = len(question_words & snippet_words)
            s += min(overlap * 0.3, 2.0)
            
            # Penalize already-fetched domains
            if result.domain in {r.domain for r in results[:3]}:
                s -= 0.5  # Encourage diversity
            
            return s
        
        return sorted(results, key=score, reverse=True)
    
    def _order_questions(self, questions: List[ResearchQuestion]) -> List[ResearchQuestion]:
        """Order questions by priority, respecting dependencies."""
        priority_order = {
            ResearchQuestionPriority.CRITICAL: 0,
            ResearchQuestionPriority.HIGH: 1,
            ResearchQuestionPriority.MEDIUM: 2,
            ResearchQuestionPriority.LOW: 3,
        }
        return sorted(questions, key=lambda q: priority_order.get(q.priority, 2))
