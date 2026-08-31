"""
Marketing Team — Main Pipeline Definition

Defines the structured pipeline stages for the marketing workflow:
  Classify → Brief → Research → Analyze → Strategize → Create → Growth → Quality → Synthesize

Each stage maps to a specific agent's responsibility.
The pipeline is adaptive — Neha's scope determination controls which stages execute.
"""

from execution.pipelines.models import (
    TeamPipeline, PipelineStage, PipelineInputContract, PipelineStatus
)

pipeline_instance = TeamPipeline(
    pipeline_id="marketing_pipeline",
    team_id="marketing",
    name="main",
    display_name="Main Marketing Team Pipeline",
    description="Adaptive marketing pipeline: Classify → Brief → Research → Analyze → Strategize → Create → Growth → Quality → Synthesize",
    version="2.0.0",
    status=PipelineStatus.ACTIVE,
    input_contract=PipelineInputContract(
        input_type="marketing_request",
        required=True,
        description="A natural language marketing request or structured MarketingBrief object"
    ),
    output_contract_id="marketing_artifact",
    stages=[
        PipelineStage(
            stage_id="classify",
            name="classify",
            display_name="Classify & Scope",
            description="Neha classifies the request type and determines the appropriate scope level "
                        "(minimal/focused/standard/comprehensive/full). This controls which downstream stages execute.",
            order=1,
            stage_definition_id="marketing_classify_def",
            required=True,
            max_attempts=2,
            retryable=True,
            metadata={"agent": "Neha", "role": "Marketing Strategist"}
        ),
        PipelineStage(
            stage_id="brief",
            name="brief",
            display_name="Create Brief",
            description="Neha creates a structured MarketingBrief from the request, "
                        "capturing business context, audience, objectives, constraints, and requirements.",
            order=2,
            stage_definition_id="marketing_brief_def",
            depends_on=["classify"],
            required=True,
            max_attempts=2,
            retryable=True,
            metadata={"agent": "Neha", "role": "Marketing Strategist"}
        ),
        PipelineStage(
            stage_id="research",
            name="research",
            display_name="Market Research",
            description="Dev coordinates with the Research Team to gather market intelligence, "
                        "competitor data, and audience insights. Conditional — only runs when "
                        "Neha's scope assessment indicates research is needed.",
            order=3,
            stage_definition_id="marketing_research_def",
            depends_on=["brief"],
            required=False,
            max_attempts=2,
            retryable=True,
            metadata={"agent": "Dev", "role": "Marketing Analyst", "conditional": True}
        ),
        PipelineStage(
            stage_id="analyze",
            name="analyze",
            display_name="Market Analysis",
            description="Dev analyzes research findings: builds competitor profiles, "
                        "defines audience segments, creates SEO plans, and extracts "
                        "marketing-specific intelligence from raw research data.",
            order=4,
            stage_definition_id="marketing_analyze_def",
            depends_on=["research"],
            required=True,
            max_attempts=2,
            retryable=True,
            metadata={"agent": "Dev", "role": "Marketing Analyst"}
        ),
        PipelineStage(
            stage_id="strategize",
            name="strategize",
            display_name="Strategy Development",
            description="Neha creates the marketing strategy: positioning, messaging framework, "
                        "channel selection, campaign architecture, KPIs, and cross-team needs. "
                        "Integrates research findings into strategic decisions.",
            order=5,
            stage_definition_id="marketing_strategize_def",
            depends_on=["analyze"],
            required=True,
            max_attempts=2,
            retryable=True,
            metadata={"agent": "Neha", "role": "Marketing Strategist"}
        ),
        PipelineStage(
            stage_id="create",
            name="create",
            display_name="Content Creation",
            description="Karan produces channel-native marketing content: social posts, blog posts, "
                        "email campaigns, ad copy, landing page copy, and content calendars. "
                        "All content respects brand voice and strategy.",
            order=6,
            stage_definition_id="marketing_create_def",
            depends_on=["strategize"],
            required=True,
            max_attempts=2,
            retryable=True,
            metadata={"agent": "Karan", "role": "Content Creator"}
        ),
        PipelineStage(
            stage_id="growth",
            name="growth",
            display_name="Growth Planning",
            description="Simran designs growth plan: funnel analysis, growth loops, "
                        "acquisition strategy, experiments with proper methodology, "
                        "and retention strategies.",
            order=7,
            stage_definition_id="marketing_growth_def",
            depends_on=["strategize"],
            required=False,
            max_attempts=1,
            retryable=False,
            metadata={"agent": "Simran", "role": "Growth Specialist", "conditional": True}
        ),
        PipelineStage(
            stage_id="quality",
            name="quality",
            display_name="Quality Gate",
            description="Multi-dimensional quality evaluation: strategic coherence, "
                        "brand consistency, factual accuracy, content quality, "
                        "and actionability assessment.",
            order=8,
            stage_definition_id="marketing_quality_def",
            depends_on=["create"],
            required=True,
            max_attempts=1,
            retryable=False,
            metadata={"threshold": 50, "evaluator": "Neha"}
        ),
        PipelineStage(
            stage_id="synthesize",
            name="synthesize",
            display_name="Synthesize & Report",
            description="Neha synthesizes all outputs into a structured MarketingArtifact "
                        "and generates a user-facing report with executive summary, "
                        "next actions, and cross-team handoff items.",
            order=9,
            stage_definition_id="marketing_synthesize_def",
            depends_on=["quality"],
            required=True,
            max_attempts=1,
            retryable=False,
            metadata={"agent": "Neha", "role": "Marketing Strategist"}
        ),
    ],
    pipeline_gate_ids=["marketing_quality_gate"],
)
