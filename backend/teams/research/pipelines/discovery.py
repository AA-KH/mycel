from execution.pipelines.models import TeamPipeline, PipelineStage, PipelineInputContract, PipelineStatus

pipeline_instance = TeamPipeline(
    pipeline_id="research_discovery",
    team_id="research",
    name="discovery",
    display_name="Discovery Pipeline",
    status=PipelineStatus.ACTIVE,
    input_contract=PipelineInputContract(input_type="standard_task"),
    stages=[
        PipelineStage(
            stage_id="discover",
            name="discover",
            display_name="Discover",
            order=1,
            stage_definition_id="discover_def"
        ),
        PipelineStage(
            stage_id="collect",
            name="collect",
            display_name="Collect",
            order=2,
            stage_definition_id="collect_def"
        ),
        PipelineStage(
            stage_id="verify",
            name="verify",
            display_name="Verify",
            order=3,
            stage_definition_id="verify_def"
        ),
        PipelineStage(
            stage_id="synthesize",
            name="synthesize",
            display_name="Synthesize",
            order=4,
            stage_definition_id="synthesize_def"
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
