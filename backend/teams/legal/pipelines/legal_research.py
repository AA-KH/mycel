from execution.pipelines.models import TeamPipeline, PipelineStage, PipelineInputContract, PipelineStatus

pipeline_instance = TeamPipeline(
    pipeline_id="legal_legal_research",
    team_id="legal",
    name="legal_research",
    display_name="Legal Research Pipeline",
    status=PipelineStatus.ACTIVE,
    input_contract=PipelineInputContract(input_type="standard_task"),
    stages=[
        PipelineStage(
            stage_id="legal_research",
            name="legal_research",
            display_name="Legal Research",
            order=1,
            stage_definition_id="legal_research_def"
        ),
        PipelineStage(
            stage_id="authority_verification",
            name="authority_verification",
            display_name="Authority Verification",
            order=2,
            stage_definition_id="authority_verification_def"
        ),
        PipelineStage(
            stage_id="analysis",
            name="analysis",
            display_name="Analysis",
            order=3,
            stage_definition_id="analysis_def"
        ),
        PipelineStage(
            stage_id="drafting",
            name="drafting",
            display_name="Drafting",
            order=4,
            stage_definition_id="drafting_def"
        ),
        PipelineStage(
            stage_id="review",
            name="review",
            display_name="Review",
            order=5,
            stage_definition_id="review_def"
        )
    ]
)
