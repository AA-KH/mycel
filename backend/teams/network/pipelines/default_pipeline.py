from execution.pipelines.models import TeamPipeline, PipelineInputContract, PipelineStatus

pipeline_instance = TeamPipeline(
    pipeline_id="network_default",
    team_id="network",
    name="default_network_pipeline",
    display_name="Default Network Pipeline",
    description="Standard execution pipeline for network tasks.",
    status=PipelineStatus.ACTIVE,
    input_contract=PipelineInputContract(
        input_type="task_request",
        required=True,
        description="Standard task input"
    ),
    stages=[]
)
