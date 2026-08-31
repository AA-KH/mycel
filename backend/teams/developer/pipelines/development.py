from execution.pipelines.models import TeamPipeline, PipelineStage, PipelineInputContract, PipelineStatus

pipeline_instance = TeamPipeline(
    pipeline_id="developer_development",
    team_id="developer",
    name="development",
    display_name="Development Pipeline",
    status=PipelineStatus.ACTIVE,
    input_contract=PipelineInputContract(input_type="standard_task"),
    stages=[
        PipelineStage(
            stage_id="research",
            name="research",
            display_name="Research",
            order=1,
            stage_definition_id="research_def"
        ),
        PipelineStage(
            stage_id="architecture",
            name="architecture",
            display_name="Architecture",
            order=2,
            stage_definition_id="architecture_def"
        ),
        PipelineStage(
            stage_id="development",
            name="development",
            display_name="Development",
            order=3,
            stage_definition_id="development_def"
        ),
        PipelineStage(
            stage_id="testing",
            name="testing",
            display_name="Testing",
            order=4,
            stage_definition_id="testing_def"
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
