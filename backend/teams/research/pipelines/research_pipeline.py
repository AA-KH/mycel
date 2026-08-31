"""
Research Team — Main Pipeline Definition

Defines the structured pipeline stages for the research workflow:
  Analyze → Research → Verify → Synthesize → Review

Each stage maps to a specific agent's responsibility.
"""

from execution.pipelines.models import (
    TeamPipeline, PipelineStage, PipelineInputContract, PipelineStatus
)

pipeline_instance = TeamPipeline(
    pipeline_id="research_pipeline",
    team_id="research",
    name="main",
    display_name="Main Research Team Pipeline",
    description="Evidence-based research pipeline: Plan → Investigate → Verify → Synthesize → Review",
    version="2.0.0",
    status=PipelineStatus.ACTIVE,
    input_contract=PipelineInputContract(
        input_type="research_request",
        required=True,
        description="A natural language research request or structured ResearchRequest object"
    ),
    output_contract_id="research_artifact",
    stages=[
        PipelineStage(
            stage_id="analyze",
            name="analyze",
            display_name="Analyze & Plan",
            description="Meera decomposes the research request into a structured ResearchPlan with specific questions, "
                        "search strategies, and acceptance criteria.",
            order=1,
            stage_definition_id="research_analyze_def",
            required=True,
            max_attempts=2,
            retryable=True,
            metadata={"agent": "Meera", "role": "Research Analyst"}
        ),
        PipelineStage(
            stage_id="research",
            name="research",
            display_name="Research & Investigate",
            description="Aarav executes iterative web research: search → fetch → extract evidence → "
                        "identify gaps → refine queries → collect claims with full provenance.",
            order=2,
            stage_definition_id="research_investigate_def",
            depends_on=["analyze"],
            required=True,
            max_attempts=2,
            retryable=True,
            metadata={"agent": "Aarav", "role": "Researcher"}
        ),
        PipelineStage(
            stage_id="verify",
            name="verify",
            display_name="Verify & Fact-Check",
            description="Aditya independently verifies claims through separate search. "
                        "Never manufactures certainty. Detects source conflicts.",
            order=3,
            stage_definition_id="research_verify_def",
            depends_on=["research"],
            required=True,
            max_attempts=1,
            retryable=False,
            metadata={"agent": "Aditya", "role": "Fact Checker"}
        ),
        PipelineStage(
            stage_id="synthesize",
            name="synthesize",
            display_name="Synthesize & Report",
            description="Nisha synthesizes verified claims into a structured ResearchArtifact, "
                        "user-facing report, and downstream context.",
            order=4,
            stage_definition_id="research_synthesize_def",
            depends_on=["verify"],
            required=True,
            max_attempts=2,
            retryable=True,
            metadata={"agent": "Nisha", "role": "Research Writer"}
        ),
        PipelineStage(
            stage_id="review",
            name="review",
            display_name="Quality Review",
            description="Quality gate: evaluate research quality score. "
                        "If below threshold, can trigger re-investigation.",
            order=5,
            stage_definition_id="research_review_def",
            depends_on=["synthesize"],
            required=True,
            max_attempts=1,
            retryable=False,
            metadata={"threshold": 30, "evaluator": "Orchestrator"}
        ),
    ],
    pipeline_gate_ids=["research_quality_gate", "evidence_quality_gate"],
)
