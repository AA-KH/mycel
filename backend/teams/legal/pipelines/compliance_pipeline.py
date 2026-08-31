from execution.pipelines.models import TeamPipeline, PipelineStage, PipelineInputContract, PipelineStatus

pipeline_instance = TeamPipeline(
    pipeline_id="compliance_pipeline",
    team_id="legal",
    name="compliance",
    display_name="Compliance Pipeline",
    status=PipelineStatus.ACTIVE,
    input_contract=PipelineInputContract(input_type="compliance_request"),
    output_contract_id="compliance_report",
    stages=[
        PipelineStage(
            stage_id="requirement_identification",
            name="requirement_identification",
            display_name="Requirement Identification",
            order=1,
            stage_definition_id="requirement_identification_def"
        ),
        PipelineStage(
            stage_id="risk_assessment",
            name="risk_assessment",
            display_name="Risk Assessment",
            order=2,
            stage_definition_id="risk_assessment_def"
        ),
        PipelineStage(
            stage_id="gap_analysis",
            name="gap_analysis",
            display_name="Gap Analysis",
            order=3,
            stage_definition_id="gap_analysis_def"
        ),
        PipelineStage(
            stage_id="mitigation_planning",
            name="mitigation_planning",
            display_name="Mitigation Planning",
            order=4,
            stage_definition_id="mitigation_planning_def"
        ),
        PipelineStage(
            stage_id="report_generation",
            name="report_generation",
            display_name="Report Generation",
            order=5,
            stage_definition_id="report_generation_def"
        )
    ]
)
