from execution.pipelines.models import TeamPipeline, PipelineInputContract

pipeline_instance = TeamPipeline(
    pipeline_id="development_pipeline",
    team_id="developer",
    name="main",
    display_name="Main Developer Team Pipeline",
    input_contract=PipelineInputContract(input_type="task"),
    output_contract_id="source_code",
    stages=[]
)
