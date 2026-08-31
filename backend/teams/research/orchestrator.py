"""
Research Team Orchestrator

Drives the full research pipeline:
  Meera (plan) → Aarav (investigate) → Aditya (verify) → Nisha (synthesize)

Integrates with the Mycel infrastructure:
- RuntimeEventPublisher for real-time status updates
- task_logger for audit trail
- BaseAgent.report_status for Virtual Office UI
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from core.groq_engine import engine_manager
from core.task_logger import log_team_result
from agents.base_agent import BaseAgent
from teams.research.models import ResearchArtifact, ResearchTrace
from teams.research.agents.meera import MeeraResearchAnalyst
from teams.research.agents.aarav import AaravResearcher
from teams.research.agents.aditya import AdityaFactChecker
from teams.research.agents.nisha import NishaResearchWriter
from teams.research.engine.search import SearchEngine
from teams.research.engine.fetcher import ContentFetcher

logger = logging.getLogger(__name__)


class ResearchTeamOrchestrator(BaseAgent):
    """
    Orchestrates the Research Team pipeline.
    
    Pipeline:
    1. PLAN (Meera) — Decompose request into research questions
    2. INVESTIGATE (Aarav) — Search, fetch, extract evidence & claims
    3. VERIFY (Aditya) — Independent fact-checking of claims
    4. SYNTHESIZE (Nisha) — Write report + build downstream context
    
    Quality gate: If quality score < threshold, can loop back to step 2
    with refined questions from unresolved gaps.
    """
    
    def __init__(self, task_id: str, user_id: str = "system"):
        super().__init__(
            name="Research Team",
            role="research",
            system_prompt="Research Team Orchestrator",
            user_id=user_id
        )
        self.task_id = task_id
        self.team = "research"
        self.employee_name = "Research Team"
        
        # Shared trace across all agents
        self.trace = ResearchTrace()
        
        # Shared engine instances (Aarav and Aditya get separate ones for independence)
        self._search_engine_aarav = SearchEngine()
        self._search_engine_aditya = SearchEngine()  # Separate for independent verification
        self._fetcher_aarav = ContentFetcher()
        self._fetcher_aditya = ContentFetcher()  # Separate for independent verification
    
    async def run_task(self, task_description: str, model: str = "qwen/qwen3.8-27b") -> str:
        """
        Main entry point — runs the full research pipeline.
        Returns the final research report as a string.
        
        Overrides BaseAgent.run_task to use the multi-agent pipeline
        instead of a single LLM call.
        """
        started_at = datetime.now(timezone.utc)
        
        self.trace.log(
            agent="Orchestrator",
            action="pipeline_started",
            details=f"Research request: {task_description[:200]}",
            task_id=self.task_id
        )
        
        try:
            artifact = await self._run_pipeline(task_description)
            
            # Log to task_logger
            await log_team_result(
                self.task_id,
                "research",
                task_description,
                artifact.user_report[:5000] if artifact.user_report else "Research completed"
            )
            
            duration = (datetime.now(timezone.utc) - started_at).total_seconds()
            
            self.trace.log(
                agent="Orchestrator",
                action="pipeline_completed",
                details=f"Completed in {duration:.1f}s. Quality: {artifact.quality_score.overall_score:.0f}/100",
                task_id=self.task_id
            )
            
            await self.report_status(
                "complete",
                f"✅ Research complete — Quality: {artifact.quality_score.overall_score:.0f}/100 | "
                f"Sources: {artifact.total_sources_consulted} | "
                f"Claims: {len(artifact.claims)} ({len(artifact.verified_claims)} verified)"
            )
            
            return artifact.user_report or artifact.executive_summary
            
        except Exception as e:
            logger.error(f"[Research Orchestrator] Pipeline failed: {e}")
            await self.report_status("failure", f"Research pipeline failed: {str(e)[:100]}")
            
            self.trace.log(
                agent="Orchestrator",
                action="pipeline_failed",
                details=f"Error: {str(e)}",
                task_id=self.task_id
            )
            
            raise
    
    async def run_full(self, task_description: str) -> ResearchArtifact:
        """
        Run the full pipeline and return the structured ResearchArtifact.
        Use this when you need the full structured output, not just the report.
        """
        return await self._run_pipeline(task_description)
    
    async def _run_pipeline(self, request: str) -> ResearchArtifact:
        """Execute the 4-stage research pipeline."""
        
        # ══════════════════════════════════════════════════════════
        # STAGE 1: PLAN (Meera)
        # ══════════════════════════════════════════════════════════
        await self.report_status(
            "working",
            "📋 Meera is analyzing the research request and creating a plan..."
        )
        
        meera = MeeraResearchAnalyst(trace=self.trace)
        plan = await meera.create_research_plan(request)
        
        await self.report_status(
            "working",
            f"📋 Meera created plan: {len(plan.questions)} questions, "
            f"type={plan.research_type.value}. Handing off to Aarav..."
        )
        
        logger.info(f"[Research] Plan: {plan.interpreted_objective}, {len(plan.questions)} questions")
        
        # ══════════════════════════════════════════════════════════
        # STAGE 2: INVESTIGATE (Aarav)
        # ══════════════════════════════════════════════════════════
        await self.report_status(
            "working",
            "🔍 Aarav is investigating — searching, fetching, and analyzing sources..."
        )
        
        aarav = AaravResearcher(
            trace=self.trace,
            search_engine=self._search_engine_aarav,
            fetcher=self._fetcher_aarav
        )
        research_data = await aarav.investigate_plan(plan)
        
        sources = research_data["sources"]
        evidence = research_data["evidence"]
        claims = research_data["claims"]
        
        await self.report_status(
            "working",
            f"🔍 Aarav finished: {len(sources)} sources, {len(claims)} claims. "
            f"Handing off to Aditya for verification..."
        )
        
        logger.info(
            f"[Research] Investigation: {len(sources)} sources, "
            f"{len(evidence)} evidence, {len(claims)} claims"
        )
        
        # ══════════════════════════════════════════════════════════
        # STAGE 3: VERIFY (Aditya)
        # ══════════════════════════════════════════════════════════
        await self.report_status(
            "working",
            "🔬 Aditya is fact-checking claims with independent verification..."
        )
        
        aditya = AdityaFactChecker(
            trace=self.trace,
            search_engine=self._search_engine_aditya,
            fetcher=self._fetcher_aditya
        )
        verified_claims = await aditya.verify_claims(claims, sources, evidence)
        
        verified_count = sum(1 for c in verified_claims 
                            if c.verification_status.value in ("verified", "partially_verified"))
        disputed_count = sum(1 for c in verified_claims 
                            if c.verification_status.value == "disputed")
        
        await self.report_status(
            "working",
            f"🔬 Aditya verified: {verified_count} confirmed, {disputed_count} disputed. "
            f"Handing off to Nisha for synthesis..."
        )
        
        logger.info(
            f"[Research] Verification: {verified_count} verified, {disputed_count} disputed"
        )
        
        # ══════════════════════════════════════════════════════════
        # STAGE 4: SYNTHESIZE (Nisha)
        # ══════════════════════════════════════════════════════════
        await self.report_status(
            "working",
            "📝 Nisha is synthesizing findings into a structured research report..."
        )
        
        nisha = NishaResearchWriter(trace=self.trace)
        artifact = await nisha.synthesize(plan, sources, evidence, verified_claims)
        
        # Set search count
        artifact.total_searches_performed = (
            self._search_engine_aarav.total_searches + 
            self._search_engine_aditya.total_searches
        )
        
        logger.info(
            f"[Research] Synthesis complete. Quality: {artifact.quality_score.overall_score:.0f}/100"
        )
        
        # ══════════════════════════════════════════════════════════
        # QUALITY GATE
        # ══════════════════════════════════════════════════════════
        if artifact.quality_score.overall_score < 30 and len(plan.questions) > 0:
            logger.warning(
                f"[Research] Quality score {artifact.quality_score.overall_score:.0f} is below threshold. "
                f"This may indicate insufficient evidence or search failures."
            )
            self.trace.log(
                agent="Orchestrator",
                action="quality_warning",
                details=f"Quality score {artifact.quality_score.overall_score:.0f}/100 is low. "
                        f"{artifact.quality_score.explanation}"
            )
        
        return artifact
