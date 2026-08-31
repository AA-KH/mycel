from execution.pipelines.models import TeamPipeline, PipelineInputContract, PipelineStatus

pipeline_instance = TeamPipeline(
    pipeline_id="executive_default",
    team_id="executive",
    name="default_executive_pipeline",
    display_name="Default Executive Pipeline",
    description="Standard execution pipeline for executive tasks.",
    status=PipelineStatus.ACTIVE,
    input_contract=PipelineInputContract(
        input_type="task_request",
        required=True,
        description="Standard task input"
    ),
    stages=[]
)
