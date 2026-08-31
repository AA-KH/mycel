from execution.pipelines.models import TeamPipeline, PipelineStage, PipelineInputContract, PipelineStatus

pipeline_instance = TeamPipeline(
    pipeline_id="creative_technical_explainer",
    team_id="creative",
    name="technical_explainer",
    display_name="Technical Explainer Pipeline",
    status=PipelineStatus.ACTIVE,
    input_contract=PipelineInputContract(input_type="standard_task"),
    stages=[
        PipelineStage(
            stage_id="scripting",
            name="scripting",
            display_name="Scripting",
            order=1,
            stage_definition_id="scripting_def"
        ),
        PipelineStage(
            stage_id="animation_render",
            name="animation_render",
            display_name="Manim Animation Rendering",
            order=2,
            stage_definition_id="animation_render_def"
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
