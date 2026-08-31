"""
Dev — Marketing Analyst

The intelligence and measurement specialist of the Marketing Team.
Responsible for market analysis, competitor analysis, audience analysis,
campaign performance analysis, and all marketing research interpretation.

Dev consumes Research Team artifacts and performs marketing-specific analysis.
He never fabricates metrics — all values use DataLabel (observed/forecast/estimate/benchmark/unknown).

Dev works closely with the Research Team. When substantial external research
is required, he formulates structured research requests rather than duplicating
the Research Team's web-research infrastructure.
"""

import json
import re
import logging
from typing import Dict, Any, List, Optional

from core.groq_engine import engine_manager
from teams.marketing.models import (
    CompetitorProfile, AnalyticsReport, LabeledMetric, DataLabel,
    ChannelType, SEOPlan, TopicCluster, ContentType,
    BrandContext, MarketingTrace, Persona,
)

logger = logging.getLogger(__name__)

DEV_SYSTEM_PROMPT = """You are Dev, the Marketing Analyst at Mycel.

You are the intelligence and measurement specialist for the Marketing Team.
You think like a senior marketing analyst with deep expertise in data interpretation.

Your responsibilities:
1. Analyze market research and extract marketing implications
2. Build competitor profiles from research data
3. Analyze audiences, define ICPs, and develop personas
4. Interpret campaign performance data
5. Identify growth opportunities from analytics
6. Define SEO strategy based on audience and search behavior
7. Formulate structured research requests when more information is needed

RULES:
1. Every metric MUST be labeled: OBSERVED (real data), FORECAST (prediction), ESTIMATE (educated guess), BENCHMARK (industry standard), or UNKNOWN
2. NEVER fabricate statistics, market share, revenue, users, or customer data
3. If data is unavailable, say "Data not available" — do not guess
4. Distinguish between company marketing claims and independent evidence
5. When sources conflict, report both sides
6. Always note the confidence level of your analysis
7. Competitor analysis must be based on actual research, not assumptions

You MUST respond in valid JSON matching the schema provided."""


class DevMarketingAnalyst:
    """
    Dev — Marketing Analyst Agent

    Responsibilities:
    - Consume Research Team artifacts and extract marketing intelligence
    - Build structured competitor profiles
    - Analyze audiences and define personas
    - Analyze campaign performance
    - Create SEO plans
    - Formulate research requests for the Research Team
    """

    def __init__(self, trace: Optional[MarketingTrace] = None):
        self.name = "Dev"
        self.role = "Marketing Analyst"
        self.trace = trace or MarketingTrace()
        self._engine = engine_manager.get_engine("marketing")

    async def analyze_market(self, research_text: str, objective: str) -> str:
        """
        Analyze research findings and extract marketing-specific implications.
        Consumes Research Team output and produces marketing intelligence.
        """
        self.trace.log(
            agent=self.name,
            action="analyzing_market",
            details=f"Analyzing research for: {objective[:200]}",
            input_summary=f"Research text: {len(research_text)} chars"
        )

        prompt = f"""Analyze this research and extract marketing-specific implications.

OBJECTIVE: {objective}

RESEARCH FINDINGS:
{research_text[:4000]}

Return JSON:
{{
    "market_overview": "Summary of the market landscape",
    "market_size_signals": "Any signals about market size (label as ESTIMATE/BENCHMARK if not hard data)",
    "trends": ["trend1", "trend2"],
    "opportunities": ["opportunity1", "opportunity2"],
    "threats": ["threat1", "threat2"],
    "audience_insights": "What we know about the target audience",
    "channel_insights": "Which channels seem effective in this market",
    "competitive_landscape": "Overview of competitive dynamics",
    "key_implications": ["implication for marketing strategy"],
    "information_gaps": ["what we still don't know"],
    "confidence_level": "high|medium|low"
}}

IMPORTANT: Label any quantitative claims with their source confidence. Never invent numbers."""

        try:
            messages = [
                {"role": "system", "content": DEV_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
            response = await self._engine.chat_completion(
                model="qwen/qwen3.8-27b",
                messages=messages,
                temperature=0.3,
                max_tokens=3000
            )
            raw = response.choices[0].message.content or ""
            raw = re.sub(r'<think>.*?</think>', '', raw, flags=re.DOTALL).strip()

            json_match = re.search(r'\{.*\}', raw, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group())
                result = json.dumps(analysis, indent=2)
            else:
                result = raw

            self.trace.log(
                agent=self.name,
                action="market_analysis_complete",
                details=f"Market analysis completed for: {objective[:100]}",
                output_summary=result[:200]
            )

            return result

        except Exception as e:
            logger.error(f"[Dev] Market analysis failed: {e}")
            return json.dumps({"error": f"Market analysis failed: {str(e)[:100]}", "information_gaps": ["Full analysis needed"]})

    async def analyze_competitors(self, research_text: str,
                                  competitor_names: Optional[List[str]] = None) -> List[CompetitorProfile]:
        """Build structured competitor profiles from research data."""
        self.trace.log(
            agent=self.name,
            action="analyzing_competitors",
            details=f"Building competitor profiles from research. Names: {competitor_names}"
        )

        prompt = f"""Analyze this research and build structured competitor profiles.

RESEARCH DATA:
{research_text[:4000]}

{f'KNOWN COMPETITORS: {competitor_names}' if competitor_names else 'Identify competitors from the research data.'}

Return JSON:
{{
    "competitors": [
        {{
            "name": "Competitor name",
            "positioning": "Their positioning",
            "products": ["product1"],
            "pricing": "Pricing info or UNKNOWN",
            "target_audience": "Their target audience",
            "messaging": "Their key message",
            "channels": ["linkedin", "blog"],
            "strengths": ["strength1"],
            "weaknesses": ["weakness1"],
            "differentiators": ["differentiator1"],
            "recent_changes": ["change1"],
            "customer_sentiment": "What customers say (from reviews/forums) or UNKNOWN",
            "white_space": ["opportunity they're missing"]
        }}
    ]
}}

IMPORTANT:
- Only include information actually found in the research
- Mark unknown fields as "UNKNOWN" or empty
- Never invent pricing, revenue, user counts, or partnerships
- Note when information comes from the competitor's own marketing vs independent sources"""

        try:
            messages = [
                {"role": "system", "content": DEV_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
            response = await self._engine.chat_completion(
                model="qwen/qwen3.8-27b",
                messages=messages,
                temperature=0.3,
                max_tokens=4000
            )
            raw = response.choices[0].message.content or ""
            raw = re.sub(r'<think>.*?</think>', '', raw, flags=re.DOTALL).strip()

            json_match = re.search(r'\{.*\}', raw, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON in competitor analysis")

            data = json.loads(json_match.group())
            profiles = []

            for comp in data.get("competitors", []):
                channels = []
                for ch in comp.get("channels", []):
                    try:
                        channels.append(ChannelType(ch))
                    except ValueError:
                        pass

                profile = CompetitorProfile(
                    name=comp.get("name", "Unknown"),
                    positioning=comp.get("positioning", ""),
                    products=comp.get("products", []),
                    pricing=comp.get("pricing", "UNKNOWN"),
                    target_audience=comp.get("target_audience", ""),
                    messaging=comp.get("messaging", ""),
                    channels=channels,
                    strengths=comp.get("strengths", []),
                    weaknesses=comp.get("weaknesses", []),
                    differentiators=comp.get("differentiators", []),
                    recent_changes=comp.get("recent_changes", []),
                    customer_sentiment=comp.get("customer_sentiment", "UNKNOWN"),
                    white_space=comp.get("white_space", []),
                    data_sources=["Research Team artifact"],
                )
                profiles.append(profile)

                self.trace.log(
                    agent=self.name,
                    action="competitor_profiled",
                    details=f"Profiled: {profile.name}"
                )

            return profiles

        except Exception as e:
            logger.error(f"[Dev] Competitor analysis failed: {e}")
            return []

    async def analyze_audience(self, research_text: str, objective: str,
                               brand_context: Optional[BrandContext] = None) -> Dict[str, Any]:
        """Analyze audience from research data. Defines ICP and personas."""
        self.trace.log(
            agent=self.name,
            action="analyzing_audience",
            details=f"Audience analysis for: {objective[:200]}"
        )

        existing_info = ""
        if brand_context:
            existing_info = f"""
Existing brand info:
- Audience: {brand_context.audience_description}
- ICP: {brand_context.icp}
- Existing personas: {len(brand_context.personas)}
"""

        prompt = f"""Analyze this research and define the target audience.

OBJECTIVE: {objective}
{existing_info}

RESEARCH DATA:
{research_text[:4000]}

Return JSON:
{{
    "audience_description": "Detailed audience description",
    "icp": "Ideal Customer Profile definition",
    "personas": [
        {{
            "name": "Persona name",
            "description": "Who they are",
            "demographics": {{"role": "value", "company_size": "value"}},
            "pain_points": ["pain1"],
            "goals": ["goal1"],
            "objections": ["objection1"],
            "preferred_channels": ["linkedin"],
            "language_patterns": ["phrases they use"],
            "jobs_to_be_done": ["jtbd1"]
        }}
    ],
    "segments": ["segment1"],
    "buying_behavior": "How they buy",
    "information_gaps": ["what we don't know about the audience"]
}}

IMPORTANT: Base personas on research evidence, not assumptions. Mark unknowns."""

        try:
            messages = [
                {"role": "system", "content": DEV_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
            response = await self._engine.chat_completion(
                model="qwen/qwen3.8-27b",
                messages=messages,
                temperature=0.3,
                max_tokens=3000
            )
            raw = response.choices[0].message.content or ""
            raw = re.sub(r'<think>.*?</think>', '', raw, flags=re.DOTALL).strip()

            json_match = re.search(r'\{.*\}', raw, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = {"audience_description": raw[:500], "information_gaps": ["Full analysis needed"]}

            self.trace.log(
                agent=self.name,
                action="audience_analysis_complete",
                details=f"ICP defined, {len(result.get('personas', []))} personas created"
            )

            return result

        except Exception as e:
            logger.error(f"[Dev] Audience analysis failed: {e}")
            return {"error": str(e), "information_gaps": ["Audience analysis failed"]}

    async def create_seo_plan(self, objective: str, audience: str,
                              research_text: str = "") -> SEOPlan:
        """Create an SEO strategy aligned with marketing objectives."""
        self.trace.log(
            agent=self.name,
            action="creating_seo_plan",
            details=f"SEO plan for: {objective[:200]}"
        )

        prompt = f"""Create an SEO strategy aligned with the marketing objective.

OBJECTIVE: {objective}
TARGET AUDIENCE: {audience}
{f'RESEARCH CONTEXT: {research_text[:2000]}' if research_text else ''}

Return JSON:
{{
    "audience": "Who we're optimizing for",
    "search_intents": ["what they search for"],
    "topic_clusters": [
        {{
            "pillar_topic": "Main topic",
            "subtopics": ["subtopic1", "subtopic2"],
            "search_intents": ["informational", "commercial"],
            "target_keywords": ["keyword1", "keyword2"],
            "content_types": ["blog_post", "guide"]
        }}
    ],
    "keyword_targets": [
        {{"keyword": "keyword", "intent": "informational|commercial|transactional|navigational", "volume_label": "ESTIMATE: high|medium|low", "difficulty_label": "ESTIMATE: high|medium|low"}}
    ],
    "content_strategy": "How content should be structured for SEO",
    "technical_requirements": ["requirement1"],
    "internal_linking_plan": "How to structure internal links",
    "aeo_geo_considerations": "AI search and GEO visibility considerations"
}}

IMPORTANT:
- Optimize for SEARCH INTENT + USER VALUE + DISCOVERABILITY
- Do not use spammy SEO tactics
- Label any volume/difficulty estimates as ESTIMATE
- Include AI-search visibility considerations where relevant"""

        try:
            messages = [
                {"role": "system", "content": DEV_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
            response = await self._engine.chat_completion(
                model="qwen/qwen3.8-27b",
                messages=messages,
                temperature=0.3,
                max_tokens=3000
            )
            raw = response.choices[0].message.content or ""
            raw = re.sub(r'<think>.*?</think>', '', raw, flags=re.DOTALL).strip()

            json_match = re.search(r'\{.*\}', raw, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON in SEO plan")

            data = json.loads(json_match.group())

            # Parse topic clusters
            clusters = []
            for tc in data.get("topic_clusters", []):
                content_types = []
                for ct in tc.get("content_types", []):
                    try:
                        content_types.append(ContentType(ct))
                    except ValueError:
                        pass
                clusters.append(TopicCluster(
                    pillar_topic=tc.get("pillar_topic", ""),
                    subtopics=tc.get("subtopics", []),
                    search_intents=tc.get("search_intents", []),
                    target_keywords=tc.get("target_keywords", []),
                    content_types=content_types,
                ))

            plan = SEOPlan(
                audience=data.get("audience", audience),
                search_intents=data.get("search_intents", []),
                topic_clusters=clusters,
                keyword_targets=data.get("keyword_targets", []),
                content_strategy=data.get("content_strategy", ""),
                technical_requirements=data.get("technical_requirements", []),
                internal_linking_plan=data.get("internal_linking_plan", ""),
                aeo_geo_considerations=data.get("aeo_geo_considerations", ""),
            )

            self.trace.log(
                agent=self.name,
                action="seo_plan_created",
                details=f"SEO plan: {len(clusters)} topic clusters, "
                        f"{len(plan.keyword_targets)} keyword targets"
            )

            return plan

        except Exception as e:
            logger.error(f"[Dev] SEO plan creation failed: {e}")
            return SEOPlan(audience=audience)

    def create_research_request(self, information_needed: List[str],
                                objective: str) -> Dict[str, Any]:
        """
        Formulate a structured research request for the Research Team.
        Dev identifies WHAT information is needed; Research Team finds it.
        """
        request = {
            "type": "marketing_research_request",
            "requested_by": self.name,
            "team": "marketing",
            "objective": objective,
            "information_needed": information_needed,
            "priority": "high",
            "expected_outputs": [
                "competitor analysis data",
                "market overview",
                "audience insights",
                "trend data"
            ],
        }

        self.trace.log(
            agent=self.name,
            action="research_requested",
            details=f"Requesting research: {len(information_needed)} items for {objective[:100]}",
            output_summary=str(information_needed[:3])
        )

        return request
