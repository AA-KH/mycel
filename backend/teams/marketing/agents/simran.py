"""
Simran — Growth Specialist

Owns acquisition, activation, retention, conversion optimization,
and experimentation for the Marketing Team.

Simran is a systems thinker who identifies bottlenecks, proposes
rigorous experiments, designs growth loops, and analyzes funnel performance.

She never calls random changes "experiments." A real experiment requires:
hypothesis → metric → baseline → intervention → result → interpretation → next action.

Simran never fabricates metrics. All data uses DataLabel.
"""

import json
import re
import logging
from typing import Dict, Any, List, Optional

from core.groq_engine import engine_manager
from teams.marketing.models import (
    GrowthExperiment, GrowthPlan, ExperimentStatus,
    LabeledMetric, DataLabel, AnalyticsReport,
    MarketingStrategy, MarketingTrace, Campaign,
    ChannelType,
)

logger = logging.getLogger(__name__)

SIMRAN_SYSTEM_PROMPT = """You are Simran, the Growth Specialist at Mycel.

You are a senior growth marketer who thinks in systems, loops, and experiments.
You focus on measurable, repeatable, scalable growth — not viral tricks.

Your responsibilities:
1. Analyze funnels and identify bottlenecks
2. Design growth loops (viral, content, referral, paid)
3. Create acquisition strategies with unit economics
4. Design rigorous growth experiments with proper methodology
5. Optimize conversion across the funnel
6. Design retention strategies
7. Analyze experiment results with statistical awareness

RULES:
1. A real experiment has: hypothesis, metric, baseline, expected result, duration, and interpretation criteria
2. NEVER call a random change an "experiment" — it needs proper methodology
3. All metrics must be labeled: OBSERVED, FORECAST, ESTIMATE, BENCHMARK, or UNKNOWN
4. Never fabricate conversion rates, CAC, LTV, or growth numbers
5. Consider statistical significance — small sample sizes don't prove anything
6. Growth must be sustainable — avoid dark patterns and manipulative tactics
7. Think in systems: input → process → output → feedback loop
8. Prioritize using ICE (Impact × Confidence × Ease) or similar frameworks

You MUST respond in valid JSON matching the schema provided."""


class SimranGrowthSpecialist:
    """
    Simran — Growth Specialist Agent

    Responsibilities:
    - Design growth plans with loops and acquisition strategies
    - Create rigorous growth experiments
    - Analyze funnels and identify bottlenecks
    - Optimize conversion
    - Evaluate experiment results
    - Design retention strategies
    """

    def __init__(self, trace: Optional[MarketingTrace] = None):
        self.name = "Simran"
        self.role = "Growth Specialist"
        self.trace = trace or MarketingTrace()
        self._engine = engine_manager.get_engine("marketing")

    async def create_growth_plan(self, strategy: MarketingStrategy,
                                 analytics_data: str = "") -> GrowthPlan:
        """
        Create a comprehensive growth plan based on strategy and any available data.
        Includes funnel analysis, growth loops, experiments, and priorities.
        """
        self.trace.log(
            agent=self.name,
            action="creating_growth_plan",
            details=f"Growth plan for: {strategy.objective[:200]}"
        )

        prompt = f"""Create a comprehensive growth plan.

MARKETING STRATEGY:
- Objective: {strategy.objective}
- Audience: {strategy.audience}
- ICP: {strategy.icp}
- Positioning: {strategy.positioning}
- Primary Channels: {[c.value for c in strategy.primary_channels]}
- KPIs: {strategy.kpis}

{f'ANALYTICS DATA: {analytics_data[:2000]}' if analytics_data else 'ANALYTICS: No existing data available — design for a new/early-stage product'}

Return JSON:
{{
    "funnel_analysis": "Analysis of the current/proposed funnel",
    "bottleneck": "Biggest growth bottleneck",
    "growth_loops": [
        "Description of growth loop 1 (e.g., content → SEO → traffic → signups → more content)",
        "Description of growth loop 2"
    ],
    "acquisition_channels": [
        "Channel 1 with rationale",
        "Channel 2 with rationale"
    ],
    "retention_strategies": [
        "Strategy 1",
        "Strategy 2"
    ],
    "referral_mechanisms": [
        "Mechanism 1"
    ],
    "cac_analysis": "CAC analysis or framework (label estimates)",
    "ltv_analysis": "LTV analysis or framework (label estimates)",
    "experiments": [
        {{
            "hypothesis": "If we [intervention], then [metric] will [change] because [reason]",
            "problem": "What problem this addresses",
            "intervention": "Specific change to make",
            "primary_metric": "What to measure",
            "baseline": "Current value or UNKNOWN",
            "expected_result": "Expected outcome",
            "duration": "How long to run",
            "target_audience": "Who to test on"
        }}
    ],
    "priorities": ["Priority 1 (highest impact)", "Priority 2"],
    "quick_wins": ["Quick win 1", "Quick win 2"]
}}

IMPORTANT:
- Growth loops must be specific and actionable, not just "go viral"
- Experiments must have real hypotheses — not "try posting more"
- Label all numeric estimates/forecasts with ESTIMATE or FORECAST
- Consider unit economics (CAC vs LTV)
- Prioritize based on impact × confidence × ease"""

        try:
            messages = [
                {"role": "system", "content": SIMRAN_SYSTEM_PROMPT},
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
                raise ValueError("No JSON in growth plan response")

            data = json.loads(json_match.group())

            # Parse experiments
            experiments = []
            for exp_data in data.get("experiments", []):
                baseline = None
                baseline_val = exp_data.get("baseline", "UNKNOWN")
                if baseline_val and baseline_val != "UNKNOWN":
                    baseline = LabeledMetric(
                        name="baseline",
                        value=baseline_val,
                        label=DataLabel.UNKNOWN,
                        source="Growth plan analysis"
                    )

                experiments.append(GrowthExperiment(
                    hypothesis=exp_data.get("hypothesis", ""),
                    problem=exp_data.get("problem", ""),
                    intervention=exp_data.get("intervention", ""),
                    target_audience=exp_data.get("target_audience", strategy.audience),
                    primary_metric=exp_data.get("primary_metric", ""),
                    baseline=baseline,
                    expected_result=exp_data.get("expected_result", ""),
                    duration=exp_data.get("duration", ""),
                    status=ExperimentStatus.HYPOTHESIS,
                ))

            plan = GrowthPlan(
                funnel_analysis=data.get("funnel_analysis", ""),
                bottleneck=data.get("bottleneck", ""),
                growth_loops=data.get("growth_loops", []),
                acquisition_channels=data.get("acquisition_channels", []),
                retention_strategies=data.get("retention_strategies", []),
                referral_mechanisms=data.get("referral_mechanisms", []),
                cac_analysis=data.get("cac_analysis", ""),
                ltv_analysis=data.get("ltv_analysis", ""),
                experiments=experiments,
                priorities=data.get("priorities", []),
                quick_wins=data.get("quick_wins", []),
            )

            self.trace.log(
                agent=self.name,
                action="growth_plan_created",
                details=f"Plan {plan.plan_id}: {len(experiments)} experiments, "
                        f"{len(plan.growth_loops)} loops, bottleneck: {plan.bottleneck[:80]}",
                output_summary=plan.bottleneck[:200]
            )

            return plan

        except Exception as e:
            logger.error(f"[Simran] Growth plan creation failed: {e}")
            return GrowthPlan(
                funnel_analysis=f"Growth plan generation failed: {str(e)[:100]}",
                priorities=["Retry growth planning with more data"],
            )

    async def create_experiment(self, hypothesis: str, metric: str,
                                intervention: str, audience: str,
                                campaign: Optional[Campaign] = None) -> GrowthExperiment:
        """
        Create a single rigorous growth experiment.
        Validates that the experiment is well-formed.
        """
        self.trace.log(
            agent=self.name,
            action="creating_experiment",
            details=f"Experiment: {hypothesis[:100]}"
        )

        # Validate hypothesis structure
        if not hypothesis or len(hypothesis) < 10:
            logger.warning("[Simran] Weak hypothesis — enriching via LLM")

        prompt = f"""Refine this growth experiment into a rigorous, measurable test.

HYPOTHESIS: {hypothesis}
PRIMARY METRIC: {metric}
INTERVENTION: {intervention}
TARGET AUDIENCE: {audience}

Return JSON:
{{
    "hypothesis": "If we [specific intervention], then [specific metric] will [specific change] because [specific reason]",
    "problem": "What specific problem this solves",
    "intervention": "Exact change to implement",
    "primary_metric": "Exact metric to measure",
    "secondary_metrics": ["secondary metric 1"],
    "expected_result": "Quantified expected outcome (labeled as FORECAST)",
    "minimum_sample_size": "Estimated minimum sample needed (or null for early stage)",
    "duration": "How long to run the experiment",
    "success_criteria": "What constitutes success",
    "risks": "What could go wrong"
}}

IMPORTANT: The hypothesis must be falsifiable. If it can't be proven wrong, it's not an experiment."""

        try:
            messages = [
                {"role": "system", "content": SIMRAN_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
            response = await self._engine.chat_completion(
                model="qwen/qwen3.8-27b",
                messages=messages,
                temperature=0.3,
                max_tokens=1500
            )
            raw = response.choices[0].message.content or ""
            raw = re.sub(r'<think>.*?</think>', '', raw, flags=re.DOTALL).strip()

            json_match = re.search(r'\{.*\}', raw, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON in experiment response")

            data = json.loads(json_match.group())

            experiment = GrowthExperiment(
                hypothesis=data.get("hypothesis", hypothesis),
                problem=data.get("problem", ""),
                intervention=data.get("intervention", intervention),
                target_audience=audience,
                primary_metric=data.get("primary_metric", metric),
                secondary_metrics=data.get("secondary_metrics", []),
                expected_result=data.get("expected_result", ""),
                minimum_sample_size=data.get("minimum_sample_size"),
                duration=data.get("duration", ""),
                status=ExperimentStatus.HYPOTHESIS,
                campaign_id=campaign.campaign_id if campaign else None,
            )

            self.trace.log(
                agent=self.name,
                action="experiment_created",
                details=f"Experiment {experiment.experiment_id}: {experiment.hypothesis[:100]}",
                experiment_id=experiment.experiment_id
            )

            return experiment

        except Exception as e:
            logger.error(f"[Simran] Experiment creation failed: {e}")
            return GrowthExperiment(
                hypothesis=hypothesis,
                intervention=intervention,
                primary_metric=metric,
                target_audience=audience,
                status=ExperimentStatus.HYPOTHESIS,
            )

    async def analyze_funnel(self, analytics_data: str, objective: str) -> Dict[str, Any]:
        """
        Analyze a marketing/sales funnel and identify bottlenecks.
        Returns structured analysis with recommendations.
        """
        self.trace.log(
            agent=self.name,
            action="analyzing_funnel",
            details=f"Funnel analysis for: {objective[:200]}"
        )

        prompt = f"""Analyze this funnel data and identify bottlenecks and opportunities.

OBJECTIVE: {objective}

DATA:
{analytics_data[:3000] if analytics_data else 'No existing funnel data — provide framework for new/early-stage product'}

Return JSON:
{{
    "funnel_stages": [
        {{
            "stage": "awareness|consideration|conversion|retention|advocacy",
            "description": "What happens at this stage",
            "estimated_performance": "ESTIMATE: description of current state",
            "bottleneck_score": "high|medium|low",
            "issues": ["issue1"],
            "opportunities": ["opportunity1"]
        }}
    ],
    "primary_bottleneck": "The biggest drop-off or issue",
    "recommendations": [
        {{
            "action": "Specific recommendation",
            "impact": "high|medium|low",
            "effort": "high|medium|low",
            "priority": 1
        }}
    ],
    "experiments_suggested": ["experiment idea 1"]
}}

IMPORTANT: Label all performance data with ESTIMATE if not from actual analytics. Never invent conversion rates."""

        try:
            messages = [
                {"role": "system", "content": SIMRAN_SYSTEM_PROMPT},
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
                result = {"primary_bottleneck": "Analysis incomplete", "recommendations": []}

            self.trace.log(
                agent=self.name,
                action="funnel_analyzed",
                details=f"Bottleneck: {result.get('primary_bottleneck', 'unknown')[:100]}",
                output_summary=str(result.get("recommendations", [])[:2])
            )

            return result

        except Exception as e:
            logger.error(f"[Simran] Funnel analysis failed: {e}")
            return {"error": str(e), "primary_bottleneck": "Analysis failed"}

    async def design_growth_loops(self, strategy: MarketingStrategy,
                                  product_description: str = "") -> List[str]:
        """
        Design specific, actionable growth loops.
        Not "go viral" but concrete feedback loops.
        """
        self.trace.log(
            agent=self.name,
            action="designing_loops",
            details=f"Growth loops for: {strategy.objective[:100]}"
        )

        prompt = f"""Design specific, actionable growth loops for this business.

STRATEGY:
- Objective: {strategy.objective}
- Audience: {strategy.audience}
- Channels: {[c.value for c in strategy.primary_channels]}
- Positioning: {strategy.positioning}

{f'PRODUCT: {product_description[:500]}' if product_description else ''}

Return JSON:
{{
    "loops": [
        {{
            "name": "Loop name",
            "type": "content|viral|referral|paid|product|community",
            "stages": ["Step 1 → ", "Step 2 → ", "Step 3 → back to Step 1"],
            "key_metric": "What to measure",
            "amplifiers": ["What makes this loop stronger"],
            "risks": ["What could break this loop"],
            "priority": "high|medium|low"
        }}
    ]
}}

IMPORTANT:
- Each loop must be a real feedback cycle, not a linear funnel
- Be specific about the mechanics — how does output feed back as input?
- Include at least one non-paid loop
- Consider the product and audience fit"""

        try:
            messages = [
                {"role": "system", "content": SIMRAN_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
            response = await self._engine.chat_completion(
                model="qwen/qwen3.8-27b",
                messages=messages,
                temperature=0.4,
                max_tokens=2500
            )
            raw = response.choices[0].message.content or ""
            raw = re.sub(r'<think>.*?</think>', '', raw, flags=re.DOTALL).strip()

            json_match = re.search(r'\{.*\}', raw, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                loops = []
                for loop in data.get("loops", []):
                    desc = f"{loop.get('name', 'Loop')}: {' → '.join(loop.get('stages', []))} (Metric: {loop.get('key_metric', 'N/A')})"
                    loops.append(desc)
                return loops
            return ["Growth loop design incomplete"]

        except Exception as e:
            logger.error(f"[Simran] Growth loop design failed: {e}")
            return [f"Growth loop design failed: {str(e)[:100]}"]

    async def evaluate_experiment(self, experiment: GrowthExperiment,
                                  result_data: str) -> GrowthExperiment:
        """
        Evaluate an experiment's results with proper statistical awareness.
        Updates experiment status, result, interpretation, and next action.
        """
        self.trace.log(
            agent=self.name,
            action="evaluating_experiment",
            details=f"Evaluating {experiment.experiment_id}: {experiment.hypothesis[:100]}",
            experiment_id=experiment.experiment_id
        )

        prompt = f"""Evaluate this growth experiment's results.

EXPERIMENT:
- Hypothesis: {experiment.hypothesis}
- Intervention: {experiment.intervention}
- Primary Metric: {experiment.primary_metric}
- Expected Result: {experiment.expected_result}
- Duration: {experiment.duration}
- Baseline: {experiment.baseline.value if experiment.baseline else 'UNKNOWN'}

RESULTS DATA:
{result_data[:2000]}

Return JSON:
{{
    "result_value": "The observed result",
    "result_label": "observed|estimate|unknown",
    "interpretation": "What this means — be honest about confidence level",
    "statistical_significance": "significant|not_significant|insufficient_data|not_applicable",
    "status": "completed|inconclusive",
    "next_action": "Specific next step based on results",
    "learnings": ["Learning 1", "Learning 2"]
}}

IMPORTANT:
- If sample size is too small, say so — don't over-interpret
- If results are ambiguous, mark as inconclusive
- Never round up to claim significance
- Be honest about what we can and cannot conclude"""

        try:
            messages = [
                {"role": "system", "content": SIMRAN_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
            response = await self._engine.chat_completion(
                model="qwen/qwen3.8-27b",
                messages=messages,
                temperature=0.2,
                max_tokens=1500
            )
            raw = response.choices[0].message.content or ""
            raw = re.sub(r'<think>.*?</think>', '', raw, flags=re.DOTALL).strip()

            json_match = re.search(r'\{.*\}', raw, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())

                try:
                    label = DataLabel(data.get("result_label", "unknown"))
                except ValueError:
                    label = DataLabel.UNKNOWN

                experiment.result = LabeledMetric(
                    name=experiment.primary_metric,
                    value=data.get("result_value", ""),
                    label=label,
                    source="Experiment evaluation"
                )
                experiment.interpretation = data.get("interpretation", "")
                experiment.statistical_significance = data.get("statistical_significance", "")
                experiment.next_action = data.get("next_action", "")

                status_map = {
                    "completed": ExperimentStatus.COMPLETED,
                    "inconclusive": ExperimentStatus.INCONCLUSIVE,
                }
                experiment.status = status_map.get(
                    data.get("status", "completed"),
                    ExperimentStatus.COMPLETED
                )

            self.trace.log(
                agent=self.name,
                action="experiment_evaluated",
                details=f"Experiment {experiment.experiment_id}: {experiment.status.value}",
                experiment_id=experiment.experiment_id,
                output_summary=experiment.interpretation[:200]
            )

            return experiment

        except Exception as e:
            logger.error(f"[Simran] Experiment evaluation failed: {e}")
            experiment.interpretation = f"Evaluation failed: {str(e)[:100]}"
            experiment.status = ExperimentStatus.INCONCLUSIVE
            return experiment
