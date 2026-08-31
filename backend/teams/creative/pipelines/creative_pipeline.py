from execution.pipelines.models import TeamPipeline, PipelineInputContract

pipeline_instance = TeamPipeline(
    pipeline_id="creative_pipeline",
    team_id="creative",
    name="main",
    display_name="Main Creative Team Pipeline",
    input_contract=PipelineInputContract(input_type="task"),
    output_contract_id="image",
    stages=[]
)
