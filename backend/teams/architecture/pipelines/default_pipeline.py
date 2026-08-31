from execution.pipelines.models import TeamPipeline, PipelineInputContract, PipelineStatus

pipeline_instance = TeamPipeline(
    pipeline_id="architecture_default",
    team_id="architecture",
    name="default_architecture_pipeline",
    display_name="Default Architecture Pipeline",
    description="Standard execution pipeline for architecture tasks.",
    status=PipelineStatus.ACTIVE,
    input_contract=PipelineInputContract(
        input_type="task_request",
        required=True,
        description="Standard task input"
    ),
    stages=[]
)
