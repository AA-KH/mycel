from execution.pipelines.models import TeamPipeline, PipelineInputContract

pipeline_instance = TeamPipeline(
    pipeline_id="finance_pipeline",
    team_id="finance",
    name="main",
    display_name="Main Finance Team Pipeline",
    input_contract=PipelineInputContract(input_type="task"),
    output_contract_id="financial_report",
    stages=[]
)
