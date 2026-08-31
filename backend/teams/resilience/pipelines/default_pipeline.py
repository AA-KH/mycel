from execution.pipelines.models import TeamPipeline, PipelineInputContract, PipelineStatus

pipeline_instance = TeamPipeline(
    pipeline_id="resilience_default",
    team_id="resilience",
    name="default_resilience_pipeline",
    display_name="Default Resilience Pipeline",
    description="Standard execution pipeline for resilience tasks.",
    status=PipelineStatus.ACTIVE,
    input_contract=PipelineInputContract(
        input_type="task_request",
        required=True,
        description="Standard task input"
    ),
    stages=[]
)
