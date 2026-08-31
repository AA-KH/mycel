from execution.pipelines.models import TeamPipeline, PipelineInputContract

pipeline_instance = TeamPipeline(
    pipeline_id="operations_pipeline",
    team_id="operations",
    name="main",
    display_name="Main Operations Team Pipeline",
    input_contract=PipelineInputContract(input_type="task"),
    output_contract_id="operations_report",
    stages=[]
)
