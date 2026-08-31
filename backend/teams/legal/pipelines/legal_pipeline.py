from execution.pipelines.models import TeamPipeline, PipelineStage, PipelineInputContract, PipelineStatus

pipeline_instance = TeamPipeline(
    pipeline_id="legal_pipeline",
    team_id="legal",
    name="main",
    display_name="Main Legal Team Pipeline",
    status=PipelineStatus.ACTIVE,
    input_contract=PipelineInputContract(input_type="standard_task"),
    output_contract_id="legal_output",
    stages=[
        PipelineStage(
            stage_id="research",
            name="research",
            display_name="Legal Research",
            order=1,
            stage_definition_id="legal_research_def"
        ),
        PipelineStage(
            stage_id="analysis",
            name="analysis",
            display_name="Document Analysis",
            order=2,
            stage_definition_id="document_analysis_def"
        ),
        PipelineStage(
            stage_id="authority_verification",
            name="authority_verification",
            display_name="Authority Verification",
            order=3,
            stage_definition_id="authority_verification_def"
        ),
        PipelineStage(
            stage_id="drafting",
            name="drafting",
            display_name="Legal Drafting",
            order=4,
            stage_definition_id="legal_drafting_def"
        ),
        PipelineStage(
            stage_id="compliance_check",
            name="compliance_check",
            display_name="Compliance Check",
            order=5,
            stage_definition_id="compliance_check_def"
        ),
        PipelineStage(
            stage_id="review",
            name="review",
            display_name="Legal Review",
            order=6,
            stage_definition_id="legal_review_def"
        ),
        PipelineStage(
            stage_id="final_approval",
            name="final_approval",
            display_name="Final Approval",
            order=7,
            stage_definition_id="final_approval_def"
        )
    ]
)
