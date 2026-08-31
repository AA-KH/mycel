"""
Marketing Team — Orchestrator

Drives the full marketing pipeline: classify → brief → research → analyze →
strategize → create → growth → quality → synthesize.

NOT every request triggers all stages. Neha's scope determination drives
which stages execute. A "Write a LinkedIn post" request skips research,
strategy, and growth. A "Launch our startup" triggers the full pipeline.

The orchestrator extends BaseAgent for status reporting (WebSocket/MongoDB)
and uses the MarketingTrace for audit.
"""

import logging
from datetime import datetime, timezone

from agents.base_agent import BaseAgent
from core.task_logger import log_team_result
from teams.marketing.models import (
    MarketingArtifact, MarketingTrace, ExecutionState,
    MarketingRequestType, ContentType, ChannelType, FunnelStage,
)
from teams.marketing.agents.neha import NehaMarketingStrategist
from teams.marketing.agents.dev import DevMarketingAnalyst
from teams.marketing.agents.karan import KaranContentCreator
from teams.marketing.agents.simran import SimranGrowthSpecialist
from teams.marketing.engine.brand_memory import BrandMemoryEngine
from teams.marketing.engine.quality import QualityEngine

logger = logging.getLogger(__name__)

ORCHESTRATOR_SYSTEM_PROMPT = """You are the Marketing Team Orchestrator at Mycel.
You coordinate the Marketing Team: Neha (Strategist), Dev (Analyst), Karan (Content Creator), and Simran (Growth Specialist).
You route work to the right agent and assemble the final output."""


class MarketingTeamOrchestrator(BaseAgent):
    """
    Marketing Team Orchestrator

    Drives the adaptive marketing pipeline:
    1. CLASSIFY — Neha classifies request and determines scope
    2. BRIEF — Neha creates marketing brief
    3. RESEARCH — Dev coordinates with Research Team (conditional)
    4. ANALYZE — Dev performs marketing-specific analysis
    5. STRATEGIZE — Neha creates marketing strategy
    6. CREATE — Karan produces content assets
    7. GROWTH — Simran designs growth plan + experiments
    8. QUALITY — Quality gate evaluation
    9. SYNTHESIZE — Assemble final MarketingArtifact + user report
    """

    def __init__(self, task_id: str = "", user_id: str = "system"):
        super().__init__(
            name="Marketing Team",
            role="marketing",
            system_prompt=ORCHESTRATOR_SYSTEM_PROMPT,
            user_id=user_id,
        )
        self.task_id = task_id

        # Shared audit trace
        self._trace = MarketingTrace()

        # Agents
        self._neha = NehaMarketingStrategist(trace=self._trace)
        self._dev = DevMarketingAnalyst(trace=self._trace)
        self._karan = KaranContentCreator(trace=self._trace)
        self._simran = SimranGrowthSpecialist(trace=self._trace)

        # Engine
        self._brand_memory = BrandMemoryEngine()
        self._quality = QualityEngine()

    async def run_task(self, task_description: str) -> str:
        """
        Main entry point — called by ManagerAgent or directly.
        Runs the adaptive marketing pipeline and returns a report.
        """
        started_at = datetime.now(timezone.utc)

        self._trace.log(
            agent="Orchestrator",
            action="pipeline_started",
            details=f"Marketing pipeline started for: {task_description[:200]}",
            task_id=self.task_id,
            input_summary=task_description[:300]
        )

        # Initialize artifact
        artifact = MarketingArtifact(
            original_request=task_description,
            trace=self._trace,
        )

        try:
            # ── Stage 1: CLASSIFY ──────────────────────────────
            await self.report_status(
                "working",
                f"🧠 Neha is analyzing the request..."
            )
            classification = await self._neha.classify_request(task_description)
            artifact.interpreted_objective = classification.get("interpreted_objective", task_description)
            artifact.request_types = [
                MarketingRequestType(rt) for rt in classification.get("request_types", ["general"])
            ]

            # Determine pipeline stages
            scope = classification.get("scope", "standard")
            stages = self._neha.get_pipeline_stages(scope)

            await self.report_status(
                "working",
                f"📋 Scope: {scope} — {len(stages)} stages. "
                f"Types: {[rt.value for rt in artifact.request_types]}"
            )

            # ── Stage 2: BRIEF ─────────────────────────────────
            if "brief" in stages:
                await self.report_status("working", "📝 Neha is creating the marketing brief...")

                # Load existing brand context
                brand_context = self._brand_memory.load_brand_context()
                artifact.brand_context = brand_context

                brief = await self._neha.create_brief(
                    task_description, classification, brand_context
                )
                artifact.brief = brief

            # ── Stage 3: RESEARCH (conditional) ────────────────
            research_text = ""
            if "research" in stages and classification.get("needs_research", False):
                await self.report_status(
                    "working",
                    "🔬 Dev is coordinating market research..."
                )
                research_text = await self._run_research_stage(
                    artifact, classification
                )

            # ── Stage 4: ANALYZE ───────────────────────────────
            if "analyze" in stages:
                await self.report_status("working", "📊 Dev is analyzing the market...")

                # Market analysis
                if research_text or artifact.brief:
                    objective = artifact.interpreted_objective
                    analysis = await self._dev.analyze_market(
                        research_text or f"Objective: {objective}",
                        objective
                    )

                    # Competitor analysis
                    competitor_profiles = await self._dev.analyze_competitors(
                        research_text or f"Analyze competitors for: {objective}",
                    )
                    artifact.competitor_profiles = competitor_profiles

                    # Audience analysis
                    audience_data = await self._dev.analyze_audience(
                        research_text or f"Analyze audience for: {objective}",
                        objective,
                        artifact.brand_context,
                    )

                    # Store analysis in trace
                    self._trace.log(
                        agent="Dev",
                        action="analysis_complete",
                        details=f"Market analysis complete. {len(competitor_profiles)} competitors profiled.",
                        output_summary=analysis[:200] if isinstance(analysis, str) else str(analysis)[:200]
                    )

            # ── Stage 5: STRATEGIZE ────────────────────────────
            if "strategize" in stages and artifact.brief:
                await self.report_status("working", "🎯 Neha is building the marketing strategy...")

                strategy = await self._neha.create_strategy(
                    artifact.brief,
                    market_analysis=research_text,
                    competitor_profiles=artifact.competitor_profiles,
                )
                artifact.strategy = strategy
                artifact.messaging_framework = strategy.messaging_framework

                # Create campaign
                campaign = await self._neha.create_campaign(strategy)
                artifact.campaigns.append(campaign)

                # Creative briefs for Creative Team
                if strategy.creative_needs:
                    from teams.marketing.models import CreativeBrief
                    for need in strategy.creative_needs[:3]:
                        cb = CreativeBrief(
                            campaign_id=campaign.campaign_id,
                            objective=strategy.objective,
                            message=strategy.messaging_framework.value_proposition if strategy.messaging_framework else "",
                            audience=strategy.audience,
                            visual_direction=need,
                        )
                        artifact.creative_briefs.append(cb)

                # Developer requirements
                artifact.developer_requirements = strategy.developer_needs
                artifact.finance_requirements = strategy.finance_needs
                artifact.legal_requirements = strategy.legal_needs

                # SEO plan if relevant
                seo_types = {MarketingRequestType.SEO, MarketingRequestType.CONTENT,
                             MarketingRequestType.GTM, MarketingRequestType.LAUNCH}
                if artifact.request_types and set(artifact.request_types) & seo_types:
                    await self.report_status("working", "🔍 Dev is creating the SEO plan...")
                    seo_plan = await self._dev.create_seo_plan(
                        strategy.objective,
                        strategy.audience,
                        research_text,
                    )
                    artifact.seo_plan = seo_plan

            # ── Stage 6: CREATE ────────────────────────────────
            if "create" in stages:
                await self.report_status("working", "✍️ Karan is creating content...")
                await self._run_content_stage(artifact, classification)

            # ── Stage 7: GROWTH ────────────────────────────────
            if "growth" in stages and artifact.strategy:
                await self.report_status("working", "📈 Simran is designing the growth plan...")

                growth_plan = await self._simran.create_growth_plan(
                    artifact.strategy
                )
                artifact.growth_plan = growth_plan
                artifact.experiments = growth_plan.experiments

            # ── Stage 8: QUALITY ───────────────────────────────
            if "quality" in stages:
                await self.report_status("working", "✅ Running quality gate...")

                quality_score = await self._neha.evaluate_quality(artifact)
                artifact.quality_score = quality_score

                # Content quality checks
                for asset in artifact.content_assets:
                    content_quality = await self._karan.check_content_quality(
                        asset.content,
                        artifact.brand_context,
                        asset.content_type,
                        asset.platform,
                    )
                    asset.quality_check = content_quality.model_dump()
                    asset.brand_voice_score = content_quality.overall_score

            # ── Stage 9: SYNTHESIZE ────────────────────────────
            await self.report_status("working", "📄 Neha is writing the final report...")

            # Generate user-facing report
            user_report = await self._neha.synthesize_report(artifact)
            artifact.user_report = user_report

            # Executive summary
            artifact.executive_summary = (
                f"Marketing work completed for: {artifact.interpreted_objective}. "
                f"Scope: {scope}. "
                f"Strategy: {'✅' if artifact.strategy else '⏭️ Skipped'}. "
                f"Content: {len(artifact.content_assets)} assets. "
                f"Campaigns: {len(artifact.campaigns)}. "
                f"Experiments: {len(artifact.experiments)}. "
                f"Quality: {artifact.quality_score.overall_score:.0f}/100."
            )

            # Determine next actions
            artifact.next_actions = self._determine_next_actions(artifact)

            # Finalize
            artifact.execution_state = ExecutionState.SUCCESS
            artifact.completed_at = datetime.now(timezone.utc)

            # Risks and assumptions
            if artifact.strategy:
                artifact.risks = artifact.strategy.risks
                artifact.assumptions = artifact.strategy.assumptions

            # Save brand learnings
            if artifact.brand_context:
                self._brand_memory.save_brand_context(artifact.brand_context)

            self._trace.log(
                agent="Orchestrator",
                action="pipeline_completed",
                details=f"Pipeline completed. Quality: {artifact.quality_score.overall_score:.0f}/100",
                task_id=self.task_id
            )

            # Log to task system
            await log_team_result(
                self.task_id,
                "Marketing Team",
                task_description,
                artifact.executive_summary
            )

            await self.report_status(
                "complete",
                f"🎉 Marketing work complete! {artifact.executive_summary}"
            )

            return artifact.user_report

        except Exception as e:
            logger.error(f"[Marketing Orchestrator] Pipeline failed: {e}", exc_info=True)
            artifact.execution_state = ExecutionState.FAILED

            self._trace.log(
                agent="Orchestrator",
                action="pipeline_failed",
                details=f"Pipeline failed: {str(e)[:200]}",
                task_id=self.task_id
            )

            await self.report_status("failure", f"❌ Marketing pipeline failed: {str(e)[:100]}")
            return f"Marketing pipeline failed: {str(e)[:200]}\n\nPartial trace:\n{self._format_trace()}"

    async def _run_research_stage(self, artifact: MarketingArtifact,
                                   classification: dict) -> str:
        """
        Coordinate with Research Team for market/competitor/audience research.
        Returns research text for downstream consumption.
        """
        # Build research request
        information_needed = []
        for rt in artifact.request_types:
            if rt in (MarketingRequestType.COMPETITIVE_ANALYSIS, MarketingRequestType.GTM,
                      MarketingRequestType.LAUNCH, MarketingRequestType.MARKET_EXPANSION):
                information_needed.extend([
                    f"Competitive landscape for: {artifact.interpreted_objective}",
                    f"Market overview and trends for: {artifact.interpreted_objective}",
                    f"Target audience analysis for: {artifact.interpreted_objective}",
                ])
            elif rt in (MarketingRequestType.SEO, MarketingRequestType.CONTENT):
                information_needed.extend([
                    f"Content landscape and SEO opportunities for: {artifact.interpreted_objective}",
                    f"Audience search behavior for: {artifact.interpreted_objective}",
                ])
            else:
                information_needed.append(
                    f"Market research for: {artifact.interpreted_objective}"
                )

        research_request = self._dev.create_research_request(
            information_needed=list(set(information_needed))[:5],
            objective=artifact.interpreted_objective,
        )

        # Try to invoke Research Team
        try:
            from teams.research.orchestrator import ResearchTeamOrchestrator

            research_orchestrator = ResearchTeamOrchestrator(
                task_id=self.task_id, user_id=self.user_id
            )

            research_query = (
                f"Research for marketing: {artifact.interpreted_objective}. "
                f"Information needed: {'; '.join(information_needed[:3])}"
            )

            await self.report_status(
                "working",
                f"🔬 Research Team is investigating: {artifact.interpreted_objective[:60]}..."
            )

            research_result = await research_orchestrator.run_task(research_query)

            if research_result:
                artifact.research_reference_id = f"research_{self.task_id}"
                self._trace.log(
                    agent="Dev",
                    action="research_received",
                    details=f"Research Team provided {len(research_result)} chars of data",
                    input_summary=research_result[:200]
                )
                return research_result

        except ImportError:
            logger.warning("[Marketing] Research Team not available — proceeding without external research")
            self._trace.log(
                agent="Orchestrator",
                action="research_unavailable",
                details="Research Team module not available — proceeding with limited research"
            )
        except Exception as e:
            logger.error(f"[Marketing] Research Team coordination failed: {e}")
            self._trace.log(
                agent="Orchestrator",
                action="research_failed",
                details=f"Research Team failed: {str(e)[:100]}"
            )

        return ""

    async def _run_content_stage(self, artifact: MarketingArtifact,
                                 classification: dict):
        """
        Create content assets based on strategy and request type.
        Adapts content production to what's actually needed.
        """
        strategy = artifact.strategy
        campaign = artifact.campaigns[0] if artifact.campaigns else None
        brand_context = artifact.brand_context
        messaging = artifact.messaging_framework

        # Determine what content to create based on request types
        content_plan = self._plan_content(artifact)

        for item in content_plan:
            content_type = item["content_type"]
            platform = item.get("platform")
            brief = item["brief"]
            funnel_stage = item.get("funnel_stage", FunnelStage.AWARENESS)

            if content_type == ContentType.EMAIL_CAMPAIGN:
                email = await self._karan.create_email_campaign(
                    campaign_type=item.get("email_type", "nurture"),
                    audience=strategy.audience if strategy else artifact.interpreted_objective,
                    messaging=messaging,
                    brand_context=brand_context,
                )
                artifact.email_campaigns.append(email)
            else:
                asset = await self._karan.create_content(
                    content_type=content_type,
                    platform=platform,
                    brief=brief,
                    brand_context=brand_context,
                    strategy=strategy,
                    campaign=campaign,
                    funnel_stage=funnel_stage,
                )
                artifact.content_assets.append(asset)

        # Content calendar if strategy exists
        if strategy and len(artifact.content_assets) > 2:
            calendar = await self._karan.create_content_calendar(
                strategy, campaign, days=30
            )
            artifact.content_calendar = calendar

    def _plan_content(self, artifact: MarketingArtifact) -> list:
        """
        Determine what content to create based on request types and strategy.
        Adaptive — doesn't produce everything for every request.
        """
        plan = []
        types = set(rt.value for rt in artifact.request_types)
        strategy = artifact.strategy
        objective = artifact.interpreted_objective

        # Social content
        if types & {"social", "launch", "gtm", "campaign", "brand_creation", "general"}:
            platforms = []
            if strategy and strategy.primary_channels:
                social_channels = {ChannelType.LINKEDIN, ChannelType.X, ChannelType.INSTAGRAM,
                                   ChannelType.FACEBOOK, ChannelType.THREADS, ChannelType.TIKTOK}
                platforms = [c for c in strategy.primary_channels if c in social_channels]

            if not platforms:
                platforms = [ChannelType.LINKEDIN]  # Default

            for platform in platforms[:3]:
                plan.append({
                    "content_type": ContentType.SOCIAL_POST,
                    "platform": platform,
                    "brief": f"Create a {platform.value} post about: {objective}",
                    "funnel_stage": FunnelStage.AWARENESS,
                })

        # Blog / long-form content
        if types & {"content", "seo", "thought_leadership", "gtm", "launch"}:
            plan.append({
                "content_type": ContentType.BLOG_POST,
                "platform": ChannelType.BLOG,
                "brief": f"Create a blog post about: {objective}",
                "funnel_stage": FunnelStage.AWARENESS,
            })

        # Email
        if types & {"email", "launch", "gtm", "retention", "acquisition"}:
            plan.append({
                "content_type": ContentType.EMAIL_CAMPAIGN,
                "brief": f"Email campaign for: {objective}",
                "email_type": "launch" if "launch" in types else "nurture",
            })

        # Landing page copy
        if types & {"launch", "conversion_optimization", "campaign", "paid_acquisition"}:
            plan.append({
                "content_type": ContentType.LANDING_PAGE_COPY,
                "platform": ChannelType.WEBSITE,
                "brief": f"Landing page copy for: {objective}",
                "funnel_stage": FunnelStage.CONVERSION,
            })

        # Ad copy
        if types & {"paid_acquisition", "campaign"}:
            plan.append({
                "content_type": ContentType.AD_COPY,
                "platform": ChannelType.PAID_SOCIAL,
                "brief": f"Ad copy for: {objective}",
                "funnel_stage": FunnelStage.CONVERSION,
            })

        # Elevator pitch / product copy
        if types & {"brand_creation", "brand_strategy", "product_marketing"}:
            plan.append({
                "content_type": ContentType.ELEVATOR_PITCH,
                "brief": f"Elevator pitch for: {objective}",
                "funnel_stage": FunnelStage.AWARENESS,
            })

        # PR
        if types & {"pr", "launch"}:
            plan.append({
                "content_type": ContentType.PRESS_RELEASE,
                "brief": f"Press release for: {objective}",
                "funnel_stage": FunnelStage.AWARENESS,
            })

        # Fallback — always produce at least one piece
        if not plan:
            plan.append({
                "content_type": ContentType.SOCIAL_POST,
                "platform": ChannelType.LINKEDIN,
                "brief": f"Create content about: {objective}",
                "funnel_stage": FunnelStage.AWARENESS,
            })

        return plan

    def _determine_next_actions(self, artifact: MarketingArtifact) -> list:
        """Determine recommended next actions based on the marketing output."""
        actions = []

        if artifact.creative_briefs:
            actions.append(f"🎨 Hand off {len(artifact.creative_briefs)} creative briefs to the Creative Team")

        if artifact.developer_requirements:
            actions.append(f"💻 Coordinate with Developer Team: {artifact.developer_requirements[:2]}")

        if artifact.content_assets:
            draft_count = len([a for a in artifact.content_assets if a.status.value == "draft"])
            if draft_count:
                actions.append(f"✏️ Review and approve {draft_count} draft content assets")

        if artifact.experiments:
            actions.append(f"🧪 Prioritize and launch {len(artifact.experiments)} growth experiments")

        if artifact.content_calendar:
            actions.append(f"📅 Begin executing {len(artifact.content_calendar.entries)}-entry content calendar")

        if artifact.email_campaigns:
            actions.append(f"📧 Set up and test {len(artifact.email_campaigns)} email campaigns")

        if artifact.seo_plan and artifact.seo_plan.topic_clusters:
            actions.append(f"🔍 Begin creating content for {len(artifact.seo_plan.topic_clusters)} SEO topic clusters")

        if artifact.strategy and artifact.strategy.research_needs:
            actions.append(f"🔬 Request additional research: {artifact.strategy.research_needs[:2]}")

        if not actions:
            actions.append("📋 Review the marketing output and provide feedback")

        return actions

    def _format_trace(self) -> str:
        """Format trace for error reporting."""
        lines = []
        for action in self._trace.actions[-10:]:
            lines.append(f"[{action.agent}] {action.action}: {action.details[:100]}")
        return "\n".join(lines)

    async def run_full(self, request: str) -> MarketingArtifact:
        """
        Run the full pipeline and return the structured MarketingArtifact
        (not just the user report). For cross-team consumption.
        """
        started_at = datetime.now(timezone.utc)

        # Run the pipeline (which sets up the artifact internally)
        report = await self.run_task(request)

        # The artifact was built during run_task. We can reconstruct it
        # from the trace and partial results, but for simplicity,
        # we rebuild it here using a second pass.
        # In practice, run_task would store the artifact for retrieval.

        # For now, return a minimal artifact with the report
        artifact = MarketingArtifact(
            original_request=request,
            interpreted_objective=request,
            user_report=report,
            trace=self._trace,
            completed_at=datetime.now(timezone.utc),
        )

        return artifact
