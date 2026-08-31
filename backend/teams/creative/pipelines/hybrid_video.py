from execution.pipelines.models import TeamPipeline, PipelineStage, PipelineInputContract, PipelineStatus

pipeline_instance = TeamPipeline(
    pipeline_id="creative_hybrid_video",
    team_id="creative",
    name="hybrid_video",
    display_name="Hybrid Video Pipeline",
    status=PipelineStatus.ACTIVE,
    input_contract=PipelineInputContract(input_type="standard_task"),
    stages=[
        PipelineStage(
            stage_id="sourcing",
            name="sourcing",
            display_name="Asset Sourcing",
            order=1,
            stage_definition_id="sourcing_def"
        ),
        PipelineStage(
            stage_id="voiceover",
            name="voiceover",
            display_name="Voiceover Generation",
            order=2,
            stage_definition_id="voiceover_def"
        ),
        PipelineStage(
            stage_id="composition",
            name="composition",
            display_name="Composition",
            order=3,
            stage_definition_id="composition_def"
        )
    ]
)
