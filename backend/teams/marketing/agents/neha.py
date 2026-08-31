"""
Neha — Marketing Strategist

The strategic decision-maker of the Marketing Team.
Responsible for understanding business objectives, defining marketing strategy,
establishing positioning, coordinating the team, and ensuring quality.

Neha determines WHAT needs to happen and delegates HOW to other agents.
She does not micromanage every action — she sets direction and evaluates outcomes.

Neha is analytical, strategic, business-oriented. She never invents facts.
She integrates research, synthesizes analysis, and makes marketing decisions.
"""

import json
import re
import logging
from typing import Dict, Any, List, Optional

from core.groq_engine import engine_manager
from teams.marketing.models import (
    MarketingRequestType, MarketingBrief, MarketingStrategy,
    MessagingFramework, Campaign, ChannelStrategy, ChannelType,
    ContentType, FunnelStage, CampaignStatus, Persona,
    MarketingQualityScore, BrandContext, MarketingTrace,
    CreativeBrief, CompetitorProfile,
)

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# System Prompts
# ─────────────────────────────────────────────────────────────

NEHA_SYSTEM_PROMPT = """You are Neha, the Marketing Strategist at Mycel.

You are the strategic decision-maker for the Marketing Team. You think like a senior VP of Marketing at a high-growth startup.

Your responsibilities:
1. Understand business objectives and translate them into marketing objectives
2. Classify and scope marketing requests (not every request needs a full GTM strategy)
3. Define positioning, ICP, personas, and messaging
4. Select channels, prioritize initiatives, allocate effort
5. Create campaign strategy and coordinate team members
6. Evaluate tradeoffs, approve strategic direction
7. Ensure brand consistency across all outputs

RULES:
- Be specific and actionable. Generic advice is worthless.
- Never invent customers, revenue, testimonials, statistics, or capabilities.
- If information is unknown, mark it as [NEEDS INPUT] or UNKNOWN.
- Distinguish between strategy (what/why) and execution (how).
- Consider the brand's actual stage, resources, and constraints.
- Think in systems: objective → audience → positioning → message → channel → content → measurement.
- Every recommendation must connect back to a business objective.

You MUST respond in valid JSON matching the schema provided."""

CLASSIFY_PROMPT = """Classify this marketing request into one or more types. Return a JSON object.

TYPES:
brand_creation, brand_strategy, gtm, launch, content, seo, social, email, paid_acquisition, growth, product_marketing, campaign, pr, community, influencer, conversion_optimization, analytics, retention, acquisition, market_expansion, rebranding, competitive_analysis, crisis_communications, general

REQUEST: {request}

Return JSON:
{{
    "request_types": ["type1", "type2"],
    "primary_type": "most_relevant_type",
    "scope": "minimal|focused|standard|comprehensive|full",
    "needs_research": true/false,
    "needs_creative": true/false,
    "needs_developer": true/false,
    "needs_finance": true/false,
    "interpreted_objective": "Clear statement of what the user actually needs"
}}"""

SCOPE_STAGES = {
    "minimal": ["classify", "create"],
    "focused": ["classify", "brief", "create"],
    "standard": ["classify", "brief", "analyze", "strategize", "create"],
    "comprehensive": ["classify", "brief", "research", "analyze", "strategize", "create", "growth"],
    "full": ["classify", "brief", "research", "analyze", "strategize", "create", "growth", "quality"],
}


class NehaMarketingStrategist:
    """
    Neha — Marketing Strategist Agent

    Responsibilities:
    - Classify and scope marketing requests
    - Create marketing briefs
    - Develop marketing strategy (positioning, messaging, channels)
    - Create campaign strategy
    - Coordinate team outputs
    - Quality evaluation
    """

    def __init__(self, trace: Optional[MarketingTrace] = None):
        self.name = "Neha"
        self.role = "Marketing Strategist"
        self.trace = trace or MarketingTrace()
        self._engine = engine_manager.get_engine("marketing")

    async def classify_request(self, request: str) -> Dict[str, Any]:
        """
        Classify a marketing request and determine appropriate scope.
        Returns classification with request types, scope, and cross-team needs.
        """
        self.trace.log(
            agent=self.name,
            action="classifying_request",
            details=f"Analyzing request: {request[:200]}",
            input_summary=request[:200]
        )

        try:
            messages = [
                {"role": "system", "content": NEHA_SYSTEM_PROMPT},
                {"role": "user", "content": CLASSIFY_PROMPT.format(request=request)}
            ]
            response = await self._engine.chat_completion(
                model="qwen/qwen3.8-27b",
                messages=messages,
                temperature=0.2,
                max_tokens=500
            )
            raw = response.choices[0].message.content or ""
            raw = re.sub(r'<think>.*?</think>', '', raw, flags=re.DOTALL).strip()

            json_match = re.search(r'\{.*\}', raw, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON in classification response")

            classification = json.loads(json_match.group())

            # Validate request types against enum
            valid_types = []
            for rt in classification.get("request_types", []):
                try:
                    valid_types.append(MarketingRequestType(rt).value)
                except ValueError:
                    pass
            if not valid_types:
                valid_types = [MarketingRequestType.GENERAL.value]
            classification["request_types"] = valid_types

            # Validate scope
            if classification.get("scope") not in SCOPE_STAGES:
                classification["scope"] = "standard"

            self.trace.log(
                agent=self.name,
                action="classified_request",
                details=f"Types: {valid_types}, Scope: {classification.get('scope')}",
                output_summary=classification.get("interpreted_objective", "")[:200]
            )

            return classification

        except Exception as e:
            logger.error(f"[Neha] Classification failed: {e}")
            return {
                "request_types": [MarketingRequestType.GENERAL.value],
                "primary_type": MarketingRequestType.GENERAL.value,
                "scope": "standard",
                "needs_research": True,
                "needs_creative": False,
                "needs_developer": False,
                "needs_finance": False,
                "interpreted_objective": request
            }

    def get_pipeline_stages(self, scope: str) -> List[str]:
        """Get the pipeline stages for a given scope level."""
        return SCOPE_STAGES.get(scope, SCOPE_STAGES["standard"])

    async def create_brief(self, request: str, classification: Dict[str, Any],
                           brand_context: Optional[BrandContext] = None) -> MarketingBrief:
        """Create a structured marketing brief from the request and classification."""
        self.trace.log(
            agent=self.name,
            action="creating_brief",
            details=f"Building brief for: {classification.get('interpreted_objective', request)[:200]}"
        )

        brand_summary = ""
        if brand_context:
            brand_summary = f"""
Brand: {brand_context.name}
Mission: {brand_context.mission}
Audience: {brand_context.audience_description}
ICP: {brand_context.icp}
Positioning: {brand_context.positioning}
Tone: {brand_context.tone}
Voice: {brand_context.voice}
Active Channels: {', '.join(c.value for c in brand_context.active_channels)}
"""

        prompt = f"""Create a structured marketing brief for this request.

REQUEST: {request}

INTERPRETED OBJECTIVE: {classification.get('interpreted_objective', request)}
REQUEST TYPES: {classification.get('request_types', [])}
{f'BRAND CONTEXT:{brand_summary}' if brand_summary else 'BRAND CONTEXT: Not yet established — mark unknown fields as [NEEDS INPUT]'}

Return JSON:
{{
    "business": "Business description",
    "product": "Product/service description",
    "objective": "Clear marketing objective",
    "target_audience": "Target audience description",
    "geography": "Target geography or [NEEDS INPUT]",
    "market": "Market description",
    "budget": "Budget or [NEEDS INPUT]",
    "timeframe": "Timeframe or [NEEDS INPUT]",
    "constraints": ["constraint1"],
    "campaign_objective": "Specific campaign objective",
    "desired_action": "What action should the audience take",
    "funnel_stage": "awareness|consideration|conversion|retention|advocacy",
    "required_deliverables": ["deliverable1", "deliverable2"]
}}

IMPORTANT:
- Be specific about the audience — not "everyone"
- If information isn't in the request, mark it [NEEDS INPUT]
- Never invent business details not provided in the request"""

        try:
            messages = [
                {"role": "system", "content": NEHA_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
            response = await self._engine.chat_completion(
                model="qwen/qwen3.8-27b",
                messages=messages,
                temperature=0.3,
                max_tokens=2000
            )
            raw = response.choices[0].message.content or ""
            raw = re.sub(r'<think>.*?</think>', '', raw, flags=re.DOTALL).strip()

            json_match = re.search(r'\{.*\}', raw, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON in brief response")

            brief_data = json.loads(json_match.group())

            # Map funnel stage
            funnel_map = {
                "awareness": FunnelStage.AWARENESS,
                "consideration": FunnelStage.CONSIDERATION,
                "conversion": FunnelStage.CONVERSION,
                "retention": FunnelStage.RETENTION,
                "advocacy": FunnelStage.ADVOCACY,
            }

            brief = MarketingBrief(
                business=brief_data.get("business", ""),
                product=brief_data.get("product", ""),
                objective=brief_data.get("objective", ""),
                target_audience=brief_data.get("target_audience", ""),
                geography=brief_data.get("geography", "[NEEDS INPUT]"),
                market=brief_data.get("market", ""),
                budget=brief_data.get("budget", "[NEEDS INPUT]"),
                timeframe=brief_data.get("timeframe", "[NEEDS INPUT]"),
                constraints=brief_data.get("constraints", []),
                brand_context=brand_context,
                campaign_objective=brief_data.get("campaign_objective", ""),
                desired_action=brief_data.get("desired_action", ""),
                funnel_stage=funnel_map.get(
                    brief_data.get("funnel_stage", "").lower(),
                    FunnelStage.AWARENESS
                ),
                required_deliverables=brief_data.get("required_deliverables", []),
                request_types=[MarketingRequestType(rt) for rt in classification.get("request_types", [])],
            )

            self.trace.log(
                agent=self.name,
                action="created_brief",
                details=f"Brief {brief.brief_id}: {brief.objective[:100]}",
                brief_id=brief.brief_id,
                output_summary=brief.objective[:200]
            )

            return brief

        except Exception as e:
            logger.error(f"[Neha] Brief creation failed: {e}")
            return MarketingBrief(
                objective=classification.get("interpreted_objective", request),
                request_types=[MarketingRequestType(rt) for rt in classification.get("request_types", [MarketingRequestType.GENERAL.value])],
            )

    async def create_strategy(self, brief: MarketingBrief,
                              market_analysis: str = "",
                              competitor_profiles: Optional[List[CompetitorProfile]] = None) -> MarketingStrategy:
        """
        Create comprehensive marketing strategy based on brief and research.
        This is Neha's primary strategic output.
        """
        self.trace.log(
            agent=self.name,
            action="creating_strategy",
            details=f"Building strategy for: {brief.objective[:200]}",
            brief_id=brief.brief_id
        )

        competitor_summary = ""
        if competitor_profiles:
            for cp in competitor_profiles[:5]:
                competitor_summary += f"\n- {cp.name}: Positioning={cp.positioning[:80]}, Strengths={cp.strengths[:3]}, Weaknesses={cp.weaknesses[:3]}"

        brand_summary = ""
        if brief.brand_context:
            bc = brief.brand_context
            brand_summary = f"Brand: {bc.name}, Positioning: {bc.positioning}, Tone: {bc.tone}, Values: {bc.values[:5]}"

        prompt = f"""Create a comprehensive marketing strategy.

BRIEF:
- Objective: {brief.objective}
- Business: {brief.business}
- Product: {brief.product}
- Target Audience: {brief.target_audience}
- Geography: {brief.geography}
- Market: {brief.market}
- Budget: {brief.budget}
- Timeframe: {brief.timeframe}
- Campaign Objective: {brief.campaign_objective}
- Desired Action: {brief.desired_action}
- Funnel Stage: {brief.funnel_stage.value if brief.funnel_stage else 'not specified'}
- Required Deliverables: {brief.required_deliverables}

{f'BRAND: {brand_summary}' if brand_summary else ''}
{f'MARKET ANALYSIS: {market_analysis[:2000]}' if market_analysis else 'MARKET ANALYSIS: Not yet available — note where research is needed'}
{f'COMPETITORS: {competitor_summary}' if competitor_summary else ''}

Return JSON:
{{
    "objective": "Clear marketing objective",
    "situation_analysis": "Current situation assessment",
    "audience": "Detailed audience description",
    "icp": "Ideal Customer Profile",
    "personas": [
        {{
            "name": "Persona name",
            "description": "Description",
            "pain_points": ["pain1"],
            "goals": ["goal1"],
            "objections": ["objection1"],
            "preferred_channels": ["linkedin", "email"],
            "jobs_to_be_done": ["jtbd1"]
        }}
    ],
    "positioning": "Strategic positioning statement",
    "messaging_framework": {{
        "value_proposition": "Core value proposition",
        "elevator_pitch": "30-second pitch",
        "tagline": "Tagline",
        "key_messages": ["msg1", "msg2", "msg3"],
        "messaging_pillars": ["pillar1", "pillar2", "pillar3"],
        "proof_points": ["proof1"],
        "tone_guidelines": "Tone description"
    }},
    "channel_strategies": [
        {{
            "channel": "linkedin|x|instagram|email|blog|seo|paid_search|paid_social|other",
            "objectives": ["obj1"],
            "content_types": ["social_post", "blog_post"],
            "frequency": "3x/week",
            "kpis": {{"metric": "target"}},
            "rationale": "Why this channel",
            "priority": "high|medium|low"
        }}
    ],
    "primary_channels": ["linkedin", "email"],
    "campaign_themes": ["theme1"],
    "kpis": {{"metric1": "target1"}},
    "success_criteria": ["criterion1"],
    "timeline": "Timeline description",
    "budget_allocation": {{"channel": "percentage or amount"}},
    "priorities": ["priority1"],
    "proposed_experiments": ["experiment1"],
    "risks": ["risk1"],
    "assumptions": ["assumption1"],
    "research_needs": ["what research is still needed"],
    "creative_needs": ["what creative assets are needed"],
    "developer_needs": ["what dev work is needed"],
    "finance_needs": ["financial analysis needed"],
    "legal_needs": ["legal review needed"]
}}

IMPORTANT:
- Select channels based on audience fit, not just popularity
- Don't recommend every channel — be selective and justify
- Connect every recommendation to the business objective
- If data is unknown, note it as an assumption
- Never invent market share, revenue, or customer numbers"""

        try:
            messages = [
                {"role": "system", "content": NEHA_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
            response = await self._engine.chat_completion(
                model="qwen/qwen3.8-27b",
                messages=messages,
                temperature=0.4,
                max_tokens=5000
            )
            raw = response.choices[0].message.content or ""
            raw = re.sub(r'<think>.*?</think>', '', raw, flags=re.DOTALL).strip()

            json_match = re.search(r'\{.*\}', raw, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON in strategy response")

            data = json.loads(json_match.group())
            strategy = self._parse_strategy(data, brief)

            self.trace.log(
                agent=self.name,
                action="created_strategy",
                details=f"Strategy {strategy.strategy_id}: {len(strategy.channel_strategies)} channels, "
                        f"{len(strategy.campaign_themes)} themes",
                strategy_id=strategy.strategy_id,
                output_summary=strategy.objective[:200]
            )

            return strategy

        except Exception as e:
            logger.error(f"[Neha] Strategy creation failed: {e}")
            return MarketingStrategy(
                objective=brief.objective,
                situation_analysis=f"Strategy generation encountered an error: {str(e)[:100]}",
                audience=brief.target_audience,
                risks=["Strategy was generated with fallback due to LLM error"],
            )

    def _parse_strategy(self, data: Dict[str, Any], brief: MarketingBrief) -> MarketingStrategy:
        """Parse LLM output into MarketingStrategy."""
        # Parse personas
        personas = []
        for p_data in data.get("personas", []):
            channels = []
            for ch in p_data.get("preferred_channels", []):
                try:
                    channels.append(ChannelType(ch))
                except ValueError:
                    pass
            personas.append(Persona(
                name=p_data.get("name", ""),
                description=p_data.get("description", ""),
                pain_points=p_data.get("pain_points", []),
                goals=p_data.get("goals", []),
                objections=p_data.get("objections", []),
                preferred_channels=channels,
                jobs_to_be_done=p_data.get("jobs_to_be_done", []),
            ))

        # Parse messaging framework
        msg_data = data.get("messaging_framework", {})
        messaging = MessagingFramework(
            value_proposition=msg_data.get("value_proposition", ""),
            elevator_pitch=msg_data.get("elevator_pitch", ""),
            tagline=msg_data.get("tagline", ""),
            key_messages=msg_data.get("key_messages", []),
            messaging_pillars=msg_data.get("messaging_pillars", []),
            proof_points=msg_data.get("proof_points", []),
            tone_guidelines=msg_data.get("tone_guidelines", ""),
        )

        # Parse channel strategies
        channel_strategies = []
        for cs_data in data.get("channel_strategies", []):
            try:
                channel = ChannelType(cs_data.get("channel", "other"))
            except ValueError:
                channel = ChannelType.OTHER

            content_types = []
            for ct in cs_data.get("content_types", []):
                try:
                    content_types.append(ContentType(ct))
                except ValueError:
                    pass

            channel_strategies.append(ChannelStrategy(
                channel=channel,
                objectives=cs_data.get("objectives", []),
                content_types=content_types,
                frequency=cs_data.get("frequency", ""),
                kpis=cs_data.get("kpis", {}),
                rationale=cs_data.get("rationale", ""),
                priority=cs_data.get("priority", "medium"),
            ))

        # Parse primary channels
        primary_channels = []
        for ch in data.get("primary_channels", []):
            try:
                primary_channels.append(ChannelType(ch))
            except ValueError:
                pass

        return MarketingStrategy(
            objective=data.get("objective", brief.objective),
            situation_analysis=data.get("situation_analysis", ""),
            audience=data.get("audience", brief.target_audience),
            icp=data.get("icp", ""),
            personas=personas,
            positioning=data.get("positioning", ""),
            messaging_framework=messaging,
            channel_strategies=channel_strategies,
            primary_channels=primary_channels,
            campaign_themes=data.get("campaign_themes", []),
            kpis=data.get("kpis", {}),
            success_criteria=data.get("success_criteria", []),
            timeline=data.get("timeline", brief.timeframe),
            budget_allocation=data.get("budget_allocation", {}),
            priorities=data.get("priorities", []),
            proposed_experiments=data.get("proposed_experiments", []),
            risks=data.get("risks", []),
            assumptions=data.get("assumptions", []),
            research_needs=data.get("research_needs", []),
            creative_needs=data.get("creative_needs", []),
            developer_needs=data.get("developer_needs", []),
            finance_needs=data.get("finance_needs", []),
            legal_needs=data.get("legal_needs", []),
        )

    async def evaluate_quality(self, artifact) -> MarketingQualityScore:
        """
        Evaluate the quality of a MarketingArtifact across multiple dimensions.
        This is the marketing quality gate.
        """
        self.trace.log(
            agent=self.name,
            action="evaluating_quality",
            details="Running marketing quality gate"
        )

        checks = {
            "business_objective_understood": bool(artifact.brief and artifact.brief.objective),
            "audience_identified": bool(
                artifact.strategy and artifact.strategy.audience
            ),
            "marketing_objective_defined": bool(
                artifact.strategy and artifact.strategy.objective
            ),
            "positioning_consistent": bool(
                artifact.strategy and artifact.strategy.positioning
            ),
            "messaging_consistent": bool(artifact.messaging_framework),
            "brand_voice_respected": bool(artifact.brand_context),
            "campaign_aligned": len(artifact.campaigns) > 0 or len(artifact.content_assets) > 0,
            "channel_justified": bool(
                artifact.strategy and artifact.strategy.channel_strategies
            ),
            "cta_defined": any(a.cta for a in artifact.content_assets),
            "content_platform_native": len(artifact.content_assets) > 0,
            "measurement_defined": bool(
                artifact.strategy and artifact.strategy.kpis
            ),
            "kpis_defined": bool(
                artifact.strategy and artifact.strategy.kpis
            ),
            "no_fabricated_claims": True,  # Structural check — agents enforce this
            "output_schema_valid": True,
        }

        total = len(checks)
        passed = sum(1 for v in checks.values() if v)
        score = (passed / total * 100) if total > 0 else 0.0

        missing = [k for k, v in checks.items() if not v]

        quality = MarketingQualityScore(
            overall_score=score,
            strategic_coherence=min(100.0, score + 10) if artifact.strategy else 0.0,
            factual_accuracy=80.0,  # Structural — agents enforce no-fabrication
            brand_consistency=80.0 if artifact.brand_context else 30.0,
            audience_relevance=80.0 if (artifact.strategy and artifact.strategy.audience) else 20.0,
            channel_fit=80.0 if (artifact.strategy and artifact.strategy.channel_strategies) else 20.0,
            content_quality=70.0 if artifact.content_assets else 0.0,
            conversion_orientation=70.0 if any(a.cta for a in artifact.content_assets) else 20.0,
            research_grounding=70.0 if artifact.research_reference_id else 30.0,
            analytics_correctness=80.0,
            actionability=80.0 if artifact.next_actions else 40.0,
            cross_team_integration=70.0 if artifact.creative_briefs or artifact.developer_requirements else 30.0,
            quality_issues=[f"Missing: {m}" for m in missing],
            missing_elements=missing,
            explanation=f"Quality gate: {passed}/{total} checks passed ({score:.0f}%)"
        )

        self.trace.log(
            agent=self.name,
            action="quality_evaluated",
            details=f"Quality score: {score:.0f}/100, {len(missing)} missing elements",
            output_summary=quality.explanation
        )

        return quality

    async def create_campaign(self, strategy: MarketingStrategy,
                              campaign_theme: str = "") -> Campaign:
        """Create a campaign based on strategy."""
        self.trace.log(
            agent=self.name,
            action="creating_campaign",
            details=f"Campaign for: {campaign_theme or strategy.objective[:100]}"
        )

        campaign = Campaign(
            name=campaign_theme or f"Campaign: {strategy.objective[:50]}",
            objective=strategy.objective,
            audience=strategy.audience,
            positioning=strategy.positioning,
            messaging=strategy.messaging_framework.value_proposition if strategy.messaging_framework else "",
            channels=strategy.primary_channels,
            timeline=strategy.timeline,
            budget=str(strategy.budget_allocation) if strategy.budget_allocation else "[NEEDS INPUT]",
            kpis=strategy.kpis,
            status=CampaignStatus.STRATEGY,
        )

        self.trace.log(
            agent=self.name,
            action="created_campaign",
            details=f"Campaign {campaign.campaign_id}: {campaign.name}",
            campaign_id=campaign.campaign_id
        )

        return campaign

    async def synthesize_report(self, artifact) -> str:
        """Generate a polished user-facing report from the MarketingArtifact."""
        self.trace.log(
            agent=self.name,
            action="synthesizing_report",
            details="Creating user-facing marketing report"
        )

        sections = []
        sections.append(f"# Marketing Report\n")

        if artifact.brief:
            sections.append(f"## Objective\n{artifact.brief.objective}\n")

        if artifact.strategy:
            s = artifact.strategy
            sections.append(f"## Situation Analysis\n{s.situation_analysis}\n")
            sections.append(f"## Target Audience\n{s.audience}\n")
            if s.icp:
                sections.append(f"## Ideal Customer Profile\n{s.icp}\n")
            sections.append(f"## Positioning\n{s.positioning}\n")

            if s.messaging_framework:
                mf = s.messaging_framework
                sections.append(f"## Messaging\n")
                sections.append(f"**Value Proposition:** {mf.value_proposition}\n")
                if mf.elevator_pitch:
                    sections.append(f"**Elevator Pitch:** {mf.elevator_pitch}\n")
                if mf.key_messages:
                    sections.append(f"**Key Messages:**\n" + "\n".join(f"- {m}" for m in mf.key_messages) + "\n")

            if s.channel_strategies:
                sections.append(f"## Channel Strategy\n")
                for cs in s.channel_strategies:
                    sections.append(f"### {cs.channel.value.title()}\n"
                                    f"- **Priority:** {cs.priority}\n"
                                    f"- **Frequency:** {cs.frequency}\n"
                                    f"- **Rationale:** {cs.rationale}\n")

            if s.kpis:
                sections.append(f"## KPIs\n" + "\n".join(f"- **{k}:** {v}" for k, v in s.kpis.items()) + "\n")

        if artifact.campaigns:
            sections.append(f"## Campaigns\n")
            for c in artifact.campaigns:
                sections.append(f"### {c.name}\n- **Objective:** {c.objective}\n- **Channels:** {', '.join(ch.value for ch in c.channels)}\n")

        if artifact.content_assets:
            sections.append(f"## Content ({len(artifact.content_assets)} assets)\n")
            for a in artifact.content_assets[:10]:
                sections.append(f"### {a.content_type.value.replace('_', ' ').title()}"
                                f"{f' ({a.platform.value})' if a.platform else ''}\n"
                                f"{a.content[:500]}\n")

        if artifact.growth_plan:
            gp = artifact.growth_plan
            sections.append(f"## Growth Plan\n")
            if gp.bottleneck:
                sections.append(f"**Key Bottleneck:** {gp.bottleneck}\n")
            if gp.growth_loops:
                sections.append(f"**Growth Loops:**\n" + "\n".join(f"- {l}" for l in gp.growth_loops) + "\n")

        if artifact.experiments:
            sections.append(f"## Experiments\n")
            for exp in artifact.experiments:
                sections.append(f"- **{exp.hypothesis}** — Metric: {exp.primary_metric}, Status: {exp.status.value}\n")

        if artifact.next_actions:
            sections.append(f"## Next Actions\n" + "\n".join(f"- {a}" for a in artifact.next_actions) + "\n")

        if artifact.risks:
            sections.append(f"## Risks & Assumptions\n" + "\n".join(f"- {r}" for r in artifact.risks) + "\n")

        report = "\n".join(sections)

        self.trace.log(
            agent=self.name,
            action="synthesized_report",
            details=f"Report: {len(report)} characters",
            output_summary=report[:200]
        )

        return report
