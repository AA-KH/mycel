from execution.pipelines.models import TeamPipeline, PipelineInputContract, PipelineStatus

pipeline_instance = TeamPipeline(
    pipeline_id="intelligence_default",
    team_id="intelligence",
    name="default_intelligence_pipeline",
    display_name="Default Intelligence Pipeline",
    description="Standard execution pipeline for intelligence tasks.",
    status=PipelineStatus.ACTIVE,
    input_contract=PipelineInputContract(
        input_type="task_request",
        required=True,
        description="Standard task input"
    ),
    stages=[]
)
