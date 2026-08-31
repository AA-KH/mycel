from execution.pipelines.models import TeamPipeline, PipelineStage, PipelineInputContract, PipelineStatus

pipeline_instance = TeamPipeline(
    pipeline_id="contract_review_pipeline",
    team_id="legal",
    name="contract_review",
    display_name="Contract Review Pipeline",
    status=PipelineStatus.ACTIVE,
    input_contract=PipelineInputContract(input_type="contract_document"),
    output_contract_id="contract_review_report",
    stages=[
        PipelineStage(
            stage_id="contract_analysis",
            name="contract_analysis",
            display_name="Contract Analysis",
            order=1,
            stage_definition_id="contract_analysis_def"
        ),
        PipelineStage(
            stage_id="risk_assessment",
            name="risk_assessment",
            display_name="Risk Assessment",
            order=2,
            stage_definition_id="risk_assessment_def"
        ),
        PipelineStage(
            stage_id="compliance_check",
            name="compliance_check",
            display_name="Compliance Check",
            order=3,
            stage_definition_id="compliance_check_def"
        ),
        PipelineStage(
            stage_id="legal_review",
            name="legal_review",
            display_name="Legal Review",
            order=4,
            stage_definition_id="legal_review_def"
        ),
        PipelineStage(
            stage_id="recommendations",
            name="recommendations",
            display_name="Recommendations",
            order=5,
            stage_definition_id="recommendations_def"
        )
    ]
)
