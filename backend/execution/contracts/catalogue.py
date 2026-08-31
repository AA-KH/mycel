"""
Execution Contract Catalogue

Defines the canonical initial TeamExecutionContracts for all 7 Mycel core teams.
21 contracts total — 3 per team.

Contract IDs follow the pattern:
    <team_id>.<task_type>.v<version>

All contracts are ACTIVE and immutable in this version.
Pipeline IDs match those defined in teams/<team>/pipelines/*.py.

NO execution occurs here — this is pure contract definition.
"""

from execution.contracts.models import (
    TeamExecutionContract,
    ContractStatus,
    ContractInputField,
    ContractInputType,
    ContractArtifactExpectation,
    StageExpectation,
    HandoffContract,
    ExecutionConstraints,
    ContractFailureCondition,
)

# ─────────────────────────────────────────────────────────────────────────────
# Shared helpers
# ─────────────────────────────────────────────────────────────────────────────

_DEFAULT_FAILURE_CONDITIONS = [
    ContractFailureCondition.INPUT_INVALID,
    ContractFailureCondition.CAPABILITY_UNAVAILABLE,
    ContractFailureCondition.PIPELINE_UNAVAILABLE,
    ContractFailureCondition.TOOL_UNAVAILABLE,
    ContractFailureCondition.OUTPUT_MISSING,
    ContractFailureCondition.QUALITY_FAILED,
]

_DEFAULT_HANDOFF = HandoffContract()


def _text_input(input_id: str, description: str, required: bool = True) -> ContractInputField:
    return ContractInputField(
        input_id=input_id,
        type=ContractInputType.TEXT,
        description=description,
        required=required,
    )


def _doc_input(input_id: str, description: str, required: bool = True) -> ContractInputField:
    return ContractInputField(
        input_id=input_id,
        type=ContractInputType.DOCUMENT,
        description=description,
        required=required,
    )


# ─────────────────────────────────────────────────────────────────────────────
# DEVELOPER TEAM (3 contracts)
# ─────────────────────────────────────────────────────────────────────────────

developer_software_development_v1 = TeamExecutionContract(
    contract_id="developer.software_development.v1",
    team_id="developer",
    version=1,
    status=ContractStatus.ACTIVE,
    description="Full software development lifecycle: design, implementation, testing, and review.",
    accepted_task_types=["software_development", "feature_development"],
    required_inputs=[
        _text_input("requirements", "Functional and technical requirements for the feature or system."),
    ],
    optional_inputs=[
        _text_input("architecture_notes", "Existing architecture context or constraints.", required=False),
        _text_input("acceptance_criteria", "Definition of done and acceptance criteria.", required=False),
    ],
    required_skills=["programming", "software_engineering", "code_review"],
    required_tools=["git", "github", "terminal"],
    required_knowledge=["software_engineering", "design_patterns"],
    reasoning_profile="engineering_reasoning",
    pipeline_id="development_pipeline",
    stage_expectations=[
        StageExpectation(stage_id="research", required=True, expected_output="requirements_analysis"),
        StageExpectation(stage_id="architecture", required=True, expected_output="design_document"),
        StageExpectation(stage_id="development", required=True, expected_output="source_code"),
        StageExpectation(stage_id="testing", required=True, expected_output="test_results"),
        StageExpectation(stage_id="review", required=True, expected_output="reviewed_code"),
    ],
    output_contract_ids=["source_code"],
    expected_artifacts=[
        ContractArtifactExpectation(artifact_type="code", required=True, format="py", description="Working source code."),
    ],
    quality_gate_ids=["code_quality", "test_coverage"],
    completion_criteria=[
        "source_code artifact created",
        "all tests pass",
        "code review complete",
        "quality gates passed",
        "handoff ready",
    ],
    failure_conditions=_DEFAULT_FAILURE_CONDITIONS,
    handoff_contract=_DEFAULT_HANDOFF,
)

developer_bug_fix_v1 = TeamExecutionContract(
    contract_id="developer.bug_fix.v1",
    team_id="developer",
    version=1,
    status=ContractStatus.ACTIVE,
    description="Diagnose, fix, and verify a reported bug.",
    accepted_task_types=["bug_fix", "defect_resolution"],
    required_inputs=[
        _text_input("bug_report", "Description of the bug including steps to reproduce."),
        _text_input("affected_component", "The system component or module affected."),
    ],
    optional_inputs=[
        _text_input("error_logs", "Relevant error logs or stack traces.", required=False),
    ],
    required_skills=["programming", "debugging", "testing"],
    required_tools=["git", "terminal", "code_execution"],
    required_knowledge=["software_engineering"],
    reasoning_profile="engineering_reasoning",
    pipeline_id="development_pipeline",
    output_contract_ids=["source_code"],
    expected_artifacts=[
        ContractArtifactExpectation(artifact_type="code", required=True, format="py", description="Fixed source code with regression test."),
    ],
    quality_gate_ids=["code_quality", "test_coverage"],
    completion_criteria=[
        "bug root cause identified",
        "fix implemented",
        "regression test added",
        "all tests pass",
        "quality gates passed",
    ],
    failure_conditions=_DEFAULT_FAILURE_CONDITIONS,
    handoff_contract=_DEFAULT_HANDOFF,
)

developer_api_development_v1 = TeamExecutionContract(
    contract_id="developer.api_development.v1",
    team_id="developer",
    version=1,
    status=ContractStatus.ACTIVE,
    description="Design and implement a REST or GraphQL API endpoint.",
    accepted_task_types=["api_development", "endpoint_development"],
    required_inputs=[
        _text_input("api_specification", "OpenAPI spec or description of the required endpoint."),
    ],
    optional_inputs=[
        _text_input("existing_schema", "Existing database or data model schema.", required=False),
    ],
    required_skills=["programming", "api_development", "software_engineering"],
    required_tools=["git", "github", "terminal"],
    required_knowledge=["software_engineering", "design_patterns"],
    reasoning_profile="engineering_reasoning",
    pipeline_id="development_pipeline",
    output_contract_ids=["source_code"],
    expected_artifacts=[
        ContractArtifactExpectation(artifact_type="code", required=True, format="py", description="API implementation."),
    ],
    quality_gate_ids=["code_quality", "api_contract_validation"],
    completion_criteria=[
        "API endpoint implemented",
        "unit tests written",
        "API contract validated",
        "quality gates passed",
    ],
    failure_conditions=_DEFAULT_FAILURE_CONDITIONS,
    handoff_contract=_DEFAULT_HANDOFF,
)


# ─────────────────────────────────────────────────────────────────────────────
# RESEARCH TEAM (3 contracts)
# ─────────────────────────────────────────────────────────────────────────────

research_research_report_v1 = TeamExecutionContract(
    contract_id="research.research_report.v1",
    team_id="research",
    version=1,
    status=ContractStatus.ACTIVE,
    description="Produce a structured research report on a topic with verified sources.",
    accepted_task_types=["research_report", "research"],
    required_inputs=[
        _text_input("research_topic", "The subject or question to research."),
    ],
    optional_inputs=[
        _text_input("scope", "Scope constraints or specific angles to focus on.", required=False),
        _text_input("depth", "Expected depth: summary, detailed, or comprehensive.", required=False),
    ],
    required_skills=["research", "information_retrieval", "synthesis"],
    required_tools=["web_search", "document_parsing"],
    required_knowledge=["research_methodology", "source_evaluation"],
    reasoning_profile="research_verify",
    pipeline_id="research_pipeline",
    stage_expectations=[
        StageExpectation(stage_id="discover", required=True, expected_output="source_list"),
        StageExpectation(stage_id="collect", required=True, expected_output="raw_data"),
        StageExpectation(stage_id="verify", required=True, quality_requirement="source_quality"),
        StageExpectation(stage_id="synthesize", required=True, expected_output="draft_report"),
        StageExpectation(stage_id="review", required=True, expected_output="final_report"),
    ],
    output_contract_ids=["research_report"],
    expected_artifacts=[
        ContractArtifactExpectation(artifact_type="document", required=True, format="md", description="Structured research report."),
    ],
    quality_gate_ids=["source_quality", "completeness"],
    completion_criteria=[
        "research report document created",
        "sources verified",
        "quality gates passed",
        "handoff ready",
    ],
    failure_conditions=_DEFAULT_FAILURE_CONDITIONS,
    handoff_contract=_DEFAULT_HANDOFF,
)

research_fact_verification_v1 = TeamExecutionContract(
    contract_id="research.fact_verification.v1",
    team_id="research",
    version=1,
    status=ContractStatus.ACTIVE,
    description="Verify the accuracy of specific claims or facts against authoritative sources.",
    accepted_task_types=["fact_verification", "fact_check"],
    required_inputs=[
        _text_input("claims", "List of claims or statements to verify."),
    ],
    optional_inputs=[
        _text_input("context", "Additional context or background information.", required=False),
    ],
    required_skills=["fact_verification", "source_analysis", "information_retrieval"],
    required_tools=["web_search", "browser"],
    required_knowledge=["source_evaluation"],
    reasoning_profile="research_verify",
    pipeline_id="research_pipeline",
    output_contract_ids=["verification_report"],
    expected_artifacts=[
        ContractArtifactExpectation(artifact_type="document", required=True, format="md", description="Fact verification report with source citations."),
    ],
    quality_gate_ids=["source_quality"],
    completion_criteria=[
        "all claims evaluated",
        "sources cited for each claim",
        "verification report created",
        "quality gates passed",
    ],
    failure_conditions=_DEFAULT_FAILURE_CONDITIONS,
    handoff_contract=_DEFAULT_HANDOFF,
)

research_market_research_v1 = TeamExecutionContract(
    contract_id="research.market_research.v1",
    team_id="research",
    version=1,
    status=ContractStatus.ACTIVE,
    description="Conduct market research to identify trends, competitors, and opportunities.",
    accepted_task_types=["market_research"],
    required_inputs=[
        _text_input("market_topic", "The market, industry, or product category to research."),
    ],
    optional_inputs=[
        _text_input("target_geography", "Geographic scope for the research.", required=False),
        _text_input("focus_areas", "Specific areas: competitors, trends, sizing, etc.", required=False),
    ],
    required_skills=["research", "data_analysis", "synthesis"],
    required_tools=["web_search", "data_extraction"],
    required_knowledge=["research_methodology"],
    reasoning_profile="research_verify",
    pipeline_id="research_pipeline",
    output_contract_ids=["market_research_report"],
    expected_artifacts=[
        ContractArtifactExpectation(artifact_type="document", required=True, format="md", description="Market research report."),
    ],
    quality_gate_ids=["source_quality", "completeness"],
    completion_criteria=[
        "market analysis complete",
        "report artifact created",
        "quality gates passed",
    ],
    failure_conditions=_DEFAULT_FAILURE_CONDITIONS,
    handoff_contract=_DEFAULT_HANDOFF,
)


# ─────────────────────────────────────────────────────────────────────────────
# CREATIVE TEAM (3 contracts)
# ─────────────────────────────────────────────────────────────────────────────

creative_promotional_video_v1 = TeamExecutionContract(
    contract_id="creative.promotional_video.v1",
    team_id="creative",
    version=1,
    status=ContractStatus.ACTIVE,
    description=(
        "Produce a promotional video for a product or service, "
        "from concept through final delivery."
    ),
    accepted_task_types=["promotional_video", "product_video"],
    required_inputs=[
        _text_input("product_description", "Description of the product or service to promote."),
    ],
    optional_inputs=[
        _doc_input("brand_assets", "Brand guidelines, logo, or visual assets.", required=False),
        _text_input("target_audience", "Target audience demographic and profile.", required=False),
        _text_input("duration", "Target video duration in seconds.", required=False),
        _text_input("format", "Required output format (e.g. mp4, webm).", required=False),
    ],
    required_skills=["creative_ideation", "storytelling", "video_editing"],
    required_tools=["video_generation", "video_editing", "media_processing"],
    required_knowledge=["visual_communication", "storytelling"],
    reasoning_profile="creative_review",
    pipeline_id="creative_pipeline",
    stage_expectations=[
        StageExpectation(stage_id="concept", required=True, expected_output="creative_brief"),
        StageExpectation(stage_id="scripting", required=True, expected_output="script"),
        StageExpectation(stage_id="production", required=True, expected_output="raw_video"),
        StageExpectation(stage_id="editing", required=True, expected_output="edited_video"),
        StageExpectation(stage_id="quality", required=True, quality_requirement="visual_quality"),
        StageExpectation(stage_id="delivery", required=True, expected_output="final_video"),
    ],
    output_contract_ids=["promotional_video"],
    expected_artifacts=[
        ContractArtifactExpectation(
            artifact_type="video",
            required=True,
            format="mp4",
            description="Final promotional video artifact.",
        ),
    ],
    quality_gate_ids=["visual_quality", "format_validation", "content_review"],
    completion_criteria=[
        "video artifact created",
        "artifact type is video",
        "format is mp4 or configured format",
        "visual quality gate passed",
        "format validation passed",
        "content review passed",
        "final ArtifactReference created",
        "handoff ready",
    ],
    failure_conditions=[
        ContractFailureCondition.INPUT_INVALID,
        ContractFailureCondition.CAPABILITY_UNAVAILABLE,
        ContractFailureCondition.PIPELINE_UNAVAILABLE,
        ContractFailureCondition.TOOL_UNAVAILABLE,
        ContractFailureCondition.ARTIFACT_INVALID,
        ContractFailureCondition.QUALITY_FAILED,
        ContractFailureCondition.OUTPUT_MISSING,
    ],
    execution_constraints=ExecutionConstraints(
        max_tool_calls=20,
        allowed_output_types=["video"],
        partial_output_allowed=False,
    ),
    handoff_contract=_DEFAULT_HANDOFF,
)

creative_image_generation_v1 = TeamExecutionContract(
    contract_id="creative.image_generation.v1",
    team_id="creative",
    version=1,
    status=ContractStatus.ACTIVE,
    description="Generate a high-quality image asset for a specified creative purpose.",
    accepted_task_types=["image_generation", "image_asset"],
    required_inputs=[
        _text_input("image_prompt", "Description of the image to generate."),
    ],
    optional_inputs=[
        _text_input("style", "Visual style reference or mood direction.", required=False),
        _text_input("dimensions", "Required image dimensions or aspect ratio.", required=False),
    ],
    required_skills=["creative_ideation", "visual_communication"],
    required_tools=["image_generation"],
    required_knowledge=["visual_design"],
    reasoning_profile="creative_review",
    pipeline_id="creative_pipeline",
    output_contract_ids=["image_asset"],
    expected_artifacts=[
        ContractArtifactExpectation(artifact_type="image", required=True, description="Generated image asset."),
    ],
    quality_gate_ids=["visual_quality"],
    completion_criteria=[
        "image artifact created",
        "visual quality gate passed",
        "handoff ready",
    ],
    failure_conditions=_DEFAULT_FAILURE_CONDITIONS,
    handoff_contract=_DEFAULT_HANDOFF,
)

creative_creative_asset_v1 = TeamExecutionContract(
    contract_id="creative.creative_asset.v1",
    team_id="creative",
    version=1,
    status=ContractStatus.ACTIVE,
    description="Produce a general creative asset — copy, script, storyboard, or multimedia brief.",
    accepted_task_types=["creative_asset", "marketing_asset", "social_media_asset"],
    required_inputs=[
        _text_input("asset_brief", "Brief describing the required creative asset."),
    ],
    optional_inputs=[
        _text_input("brand_voice", "Brand voice and tone guidelines.", required=False),
        _text_input("platform", "Target platform or channel (e.g. Instagram, LinkedIn).", required=False),
    ],
    required_skills=["creative_ideation", "storytelling", "content_production"],
    required_tools=["image_generation", "media_processing"],
    required_knowledge=["brand_communication"],
    reasoning_profile="creative_review",
    pipeline_id="creative_pipeline",
    output_contract_ids=["creative_asset"],
    expected_artifacts=[
        ContractArtifactExpectation(artifact_type="document", required=True, description="Creative asset deliverable."),
    ],
    quality_gate_ids=["content_review"],
    completion_criteria=[
        "creative asset produced",
        "content review passed",
        "handoff ready",
    ],
    failure_conditions=_DEFAULT_FAILURE_CONDITIONS,
    handoff_contract=_DEFAULT_HANDOFF,
)


# ─────────────────────────────────────────────────────────────────────────────
# LEGAL TEAM (3 contracts)
# ─────────────────────────────────────────────────────────────────────────────

legal_legal_research_v1 = TeamExecutionContract(
    contract_id="legal.legal_research.v1",
    team_id="legal",
    version=1,
    status=ContractStatus.ACTIVE,
    description="Conduct legal research on a specific question under Indian law.",
    accepted_task_types=["legal_research"],
    required_inputs=[
        _text_input("legal_question", "The legal question or issue to research."),
    ],
    optional_inputs=[
        _text_input("jurisdiction", "Specific Indian state or federal jurisdiction.", required=False),
        _text_input("relevant_statutes", "Known relevant acts or statutes to consider.", required=False),
    ],
    required_skills=["legal_research", "citation", "legal_writing"],
    required_tools=["legal_document_parser", "document_search"],
    required_knowledge=["indian_legal_system", "indian_statutes"],
    reasoning_profile="legal_authority_verification",
    pipeline_id="legal_pipeline",
    stage_expectations=[
        StageExpectation(stage_id="legal_research", required=True, expected_output="relevant_laws"),
        StageExpectation(stage_id="authority_verification", required=True, quality_requirement="legal_citation_quality"),
        StageExpectation(stage_id="analysis", required=True, expected_output="legal_analysis"),
        StageExpectation(stage_id="review", required=True, expected_output="final_legal_memo"),
    ],
    output_contract_ids=["legal_memo"],
    expected_artifacts=[
        ContractArtifactExpectation(artifact_type="document", required=True, format="pdf", description="Legal research memo."),
    ],
    quality_gate_ids=["legal_citation_quality"],
    completion_criteria=[
        "legal memo created",
        "all citations verified",
        "citation quality gate passed",
        "handoff ready",
    ],
    failure_conditions=_DEFAULT_FAILURE_CONDITIONS,
    execution_constraints=ExecutionConstraints(requires_human_approval=True),
    handoff_contract=_DEFAULT_HANDOFF,
)

legal_contract_analysis_v1 = TeamExecutionContract(
    contract_id="legal.contract_analysis.v1",
    team_id="legal",
    version=1,
    status=ContractStatus.ACTIVE,
    description="Analyse a contract document for legal risks, obligations, and compliance under Indian law.",
    accepted_task_types=["contract_analysis", "contract_review"],
    required_inputs=[
        _doc_input("contract_document", "The contract or agreement document to analyse."),
    ],
    optional_inputs=[
        _text_input("focus_areas", "Specific clauses or risk areas to focus on.", required=False),
    ],
    required_skills=["legal_document_analysis", "contract_analysis", "legal_writing"],
    required_tools=["legal_document_parser", "document_search"],
    required_knowledge=["indian_legal_system", "indian_statutes", "legal_terminology"],
    reasoning_profile="legal_authority_verification",
    pipeline_id="legal_pipeline",
    output_contract_ids=["contract_analysis_report"],
    expected_artifacts=[
        ContractArtifactExpectation(artifact_type="document", required=True, format="pdf", description="Contract analysis report."),
    ],
    quality_gate_ids=["legal_citation_quality"],
    completion_criteria=[
        "contract analysis report created",
        "risk areas identified",
        "quality gate passed",
        "human approval obtained",
    ],
    failure_conditions=_DEFAULT_FAILURE_CONDITIONS,
    execution_constraints=ExecutionConstraints(requires_human_approval=True),
    handoff_contract=_DEFAULT_HANDOFF,
)

legal_contract_draft_v1 = TeamExecutionContract(
    contract_id="legal.contract_draft.v1",
    team_id="legal",
    version=1,
    status=ContractStatus.ACTIVE,
    description="Draft a legal contract or agreement under Indian law.",
    accepted_task_types=["contract_draft", "contract_drafting"],
    required_inputs=[
        _text_input("contract_type", "Type of contract to draft (e.g. service agreement, NDA)."),
        _text_input("parties", "Names and roles of the parties involved."),
    ],
    optional_inputs=[
        _text_input("key_terms", "Key terms, obligations, or special clauses to include.", required=False),
        _text_input("jurisdiction", "Governing jurisdiction within India.", required=False),
    ],
    required_skills=["legal_writing", "contract_analysis", "citation"],
    required_tools=["document_generation", "legal_document_parser"],
    required_knowledge=["indian_legal_system", "indian_statutes"],
    reasoning_profile="legal_authority_verification",
    pipeline_id="legal_pipeline",
    output_contract_ids=["contract_draft"],
    expected_artifacts=[
        ContractArtifactExpectation(artifact_type="document", required=True, format="pdf", description="Draft contract document."),
    ],
    quality_gate_ids=["legal_citation_quality"],
    completion_criteria=[
        "draft contract created",
        "all mandatory clauses included",
        "citation quality gate passed",
        "human approval obtained",
    ],
    failure_conditions=_DEFAULT_FAILURE_CONDITIONS,
    execution_constraints=ExecutionConstraints(requires_human_approval=True, partial_output_allowed=False),
    handoff_contract=_DEFAULT_HANDOFF,
)


# ─────────────────────────────────────────────────────────────────────────────
# MARKETING TEAM (3 contracts)
# ─────────────────────────────────────────────────────────────────────────────

marketing_campaign_v1 = TeamExecutionContract(
    contract_id="marketing.campaign.v1",
    team_id="marketing",
    version=1,
    status=ContractStatus.ACTIVE,
    description="Plan and document a marketing campaign strategy.",
    accepted_task_types=["campaign", "marketing_campaign", "market_campaign"],
    required_inputs=[
        _text_input("product_or_service", "The product or service being marketed."),
        _text_input("campaign_objective", "Primary campaign objective (e.g. awareness, lead gen)."),
    ],
    optional_inputs=[
        _text_input("target_audience", "Target audience description.", required=False),
        _text_input("budget", "Approximate campaign budget.", required=False),
        _text_input("timeline", "Campaign duration or key milestones.", required=False),
    ],
    required_skills=["campaign_planning", "audience_analysis", "content_strategy"],
    required_tools=["web_research", "analytics"],
    required_knowledge=["marketing_principles", "digital_marketing"],
    reasoning_profile="marketing_strategy",
    pipeline_id="marketing_pipeline",
    output_contract_ids=["campaign_plan"],
    expected_artifacts=[
        ContractArtifactExpectation(artifact_type="document", required=True, format="md", description="Campaign plan document."),
    ],
    quality_gate_ids=["marketing_review"],
    completion_criteria=[
        "campaign plan created",
        "target audience defined",
        "channels selected",
        "review passed",
        "handoff ready",
    ],
    failure_conditions=_DEFAULT_FAILURE_CONDITIONS,
    handoff_contract=_DEFAULT_HANDOFF,
)

marketing_content_strategy_v1 = TeamExecutionContract(
    contract_id="marketing.content_strategy.v1",
    team_id="marketing",
    version=1,
    status=ContractStatus.ACTIVE,
    description="Develop a content strategy aligned with brand and marketing goals.",
    accepted_task_types=["content_strategy"],
    required_inputs=[
        _text_input("brand_context", "Brand identity, values, and positioning."),
    ],
    optional_inputs=[
        _text_input("goals", "Marketing goals the content strategy should support.", required=False),
        _text_input("channels", "Target content channels (blog, social, email, etc.).", required=False),
    ],
    required_skills=["content_strategy", "audience_analysis", "marketing_analytics"],
    required_tools=["web_research", "analytics"],
    required_knowledge=["marketing_principles", "consumer_behavior"],
    reasoning_profile="marketing_strategy",
    pipeline_id="marketing_pipeline",
    output_contract_ids=["content_strategy_document"],
    expected_artifacts=[
        ContractArtifactExpectation(artifact_type="document", required=True, format="md", description="Content strategy document."),
    ],
    quality_gate_ids=["marketing_review"],
    completion_criteria=[
        "content strategy document created",
        "channel plan included",
        "review passed",
    ],
    failure_conditions=_DEFAULT_FAILURE_CONDITIONS,
    handoff_contract=_DEFAULT_HANDOFF,
)

marketing_marketing_plan_v1 = TeamExecutionContract(
    contract_id="marketing.marketing_plan.v1",
    team_id="marketing",
    version=1,
    status=ContractStatus.ACTIVE,
    description="Produce a comprehensive marketing plan for a product, service, or initiative.",
    accepted_task_types=["marketing_plan"],
    required_inputs=[
        _text_input("initiative", "The product, service, or initiative requiring a marketing plan."),
    ],
    optional_inputs=[
        _text_input("market_context", "Existing market research or competitive landscape.", required=False),
        _text_input("timeline", "Planning horizon (e.g. Q4, 6-months, annual).", required=False),
    ],
    required_skills=["market_research", "campaign_planning", "content_strategy"],
    required_tools=["web_research", "content_generation"],
    required_knowledge=["marketing_principles", "branding"],
    reasoning_profile="marketing_strategy",
    pipeline_id="marketing_pipeline",
    output_contract_ids=["marketing_plan"],
    expected_artifacts=[
        ContractArtifactExpectation(artifact_type="document", required=True, format="md", description="Marketing plan document."),
    ],
    quality_gate_ids=["marketing_review"],
    completion_criteria=[
        "marketing plan created",
        "all plan sections complete",
        "review passed",
    ],
    failure_conditions=_DEFAULT_FAILURE_CONDITIONS,
    handoff_contract=_DEFAULT_HANDOFF,
)


# ─────────────────────────────────────────────────────────────────────────────
# FINANCE TEAM (3 contracts)
# ─────────────────────────────────────────────────────────────────────────────

finance_financial_analysis_v1 = TeamExecutionContract(
    contract_id="finance.financial_analysis.v1",
    team_id="finance",
    version=1,
    status=ContractStatus.ACTIVE,
    description="Perform a structured financial analysis on provided data or a business scenario.",
    accepted_task_types=["financial_analysis"],
    required_inputs=[
        _text_input("financial_data", "Financial data, statements, or scenario description."),
    ],
    optional_inputs=[
        _text_input("analysis_focus", "Specific area: profitability, liquidity, growth, etc.", required=False),
        _text_input("period", "Time period for the analysis.", required=False),
    ],
    required_skills=["financial_analysis", "data_analysis", "reporting"],
    required_tools=["spreadsheet_processing", "financial_calculator"],
    required_knowledge=["accounting_fundamentals", "financial_analysis"],
    reasoning_profile="financial_validation",
    pipeline_id="finance_pipeline",
    output_contract_ids=["financial_analysis_report"],
    expected_artifacts=[
        ContractArtifactExpectation(artifact_type="document", required=True, format="pdf", description="Financial analysis report."),
    ],
    quality_gate_ids=["financial_accuracy"],
    completion_criteria=[
        "financial analysis report created",
        "key metrics calculated",
        "accuracy gate passed",
        "handoff ready",
    ],
    failure_conditions=_DEFAULT_FAILURE_CONDITIONS,
    handoff_contract=_DEFAULT_HANDOFF,
)

finance_budget_v1 = TeamExecutionContract(
    contract_id="finance.budget.v1",
    team_id="finance",
    version=1,
    status=ContractStatus.ACTIVE,
    description="Prepare a budget document for a project, department, or initiative.",
    accepted_task_types=["budget", "budgeting"],
    required_inputs=[
        _text_input("scope", "Scope of the budget: project, department, or initiative."),
        _text_input("period", "Budget period (e.g. Q1, FY2025)."),
    ],
    optional_inputs=[
        _text_input("historical_data", "Historical spending data for reference.", required=False),
        _text_input("constraints", "Budget constraints or targets.", required=False),
    ],
    required_skills=["budgeting", "financial_analysis", "reporting"],
    required_tools=["spreadsheet_processing", "data_analysis"],
    required_knowledge=["budgeting", "financial_reporting"],
    reasoning_profile="financial_validation",
    pipeline_id="finance_pipeline",
    output_contract_ids=["budget_document"],
    expected_artifacts=[
        ContractArtifactExpectation(artifact_type="document", required=True, description="Budget document."),
    ],
    quality_gate_ids=["financial_accuracy"],
    completion_criteria=[
        "budget document created",
        "all line items accounted",
        "accuracy gate passed",
    ],
    failure_conditions=_DEFAULT_FAILURE_CONDITIONS,
    handoff_contract=_DEFAULT_HANDOFF,
)

finance_financial_report_v1 = TeamExecutionContract(
    contract_id="finance.financial_report.v1",
    team_id="finance",
    version=1,
    status=ContractStatus.ACTIVE,
    description="Generate a financial report summarising performance, metrics, and recommendations.",
    accepted_task_types=["financial_report", "finance_report"],
    required_inputs=[
        _text_input("reporting_period", "Period being reported on."),
        _text_input("financial_data", "Financial data or statements to summarise."),
    ],
    optional_inputs=[
        _text_input("audience", "Target audience for the report.", required=False),
    ],
    required_skills=["reporting", "financial_analysis", "data_analysis"],
    required_tools=["spreadsheet_processing", "document_generation"],
    required_knowledge=["financial_reporting", "accounting_fundamentals"],
    reasoning_profile="financial_validation",
    pipeline_id="finance_pipeline",
    output_contract_ids=["financial_report"],
    expected_artifacts=[
        ContractArtifactExpectation(artifact_type="document", required=True, format="pdf", description="Financial report."),
    ],
    quality_gate_ids=["financial_accuracy"],
    completion_criteria=[
        "financial report created",
        "key metrics included",
        "accuracy gate passed",
    ],
    failure_conditions=_DEFAULT_FAILURE_CONDITIONS,
    handoff_contract=_DEFAULT_HANDOFF,
)


# ─────────────────────────────────────────────────────────────────────────────
# OPERATIONS TEAM (3 contracts)
# ─────────────────────────────────────────────────────────────────────────────

operations_workflow_execution_v1 = TeamExecutionContract(
    contract_id="operations.workflow_execution.v1",
    team_id="operations",
    version=1,
    status=ContractStatus.ACTIVE,
    description="Execute and coordinate a defined operational workflow or process.",
    accepted_task_types=["workflow_execution", "workflow", "process_execution"],
    required_inputs=[
        _text_input("workflow_definition", "Definition or description of the workflow to execute."),
    ],
    optional_inputs=[
        _text_input("dependencies", "External dependencies or prerequisites.", required=False),
        _text_input("deadline", "Required completion deadline.", required=False),
    ],
    required_skills=["process_management", "task_coordination", "workflow_planning"],
    required_tools=["task_management", "workflow_automation"],
    required_knowledge=["operations_management", "workflow_management"],
    reasoning_profile="operational_planning",
    pipeline_id="operations_pipeline",
    output_contract_ids=["workflow_execution_report"],
    expected_artifacts=[
        ContractArtifactExpectation(artifact_type="document", required=True, description="Workflow execution report."),
    ],
    quality_gate_ids=["operations_quality"],
    completion_criteria=[
        "all workflow steps completed",
        "execution report created",
        "quality gate passed",
        "handoff ready",
    ],
    failure_conditions=_DEFAULT_FAILURE_CONDITIONS,
    execution_constraints=ExecutionConstraints(partial_output_allowed=True),
    handoff_contract=_DEFAULT_HANDOFF,
)

operations_process_analysis_v1 = TeamExecutionContract(
    contract_id="operations.process_analysis.v1",
    team_id="operations",
    version=1,
    status=ContractStatus.ACTIVE,
    description="Analyse an existing operational process for efficiency, bottlenecks, and improvement opportunities.",
    accepted_task_types=["process_analysis"],
    required_inputs=[
        _text_input("process_description", "Description of the current process to analyse."),
    ],
    optional_inputs=[
        _text_input("metrics", "Current performance metrics or KPIs.", required=False),
        _text_input("goals", "Desired improvement goals or targets.", required=False),
    ],
    required_skills=["operations_analysis", "process_management", "documentation"],
    required_tools=["task_management", "document_processing"],
    required_knowledge=["process_design", "operations_management"],
    reasoning_profile="operational_planning",
    pipeline_id="operations_pipeline",
    output_contract_ids=["process_analysis_report"],
    expected_artifacts=[
        ContractArtifactExpectation(artifact_type="document", required=True, format="md", description="Process analysis report."),
    ],
    quality_gate_ids=["operations_quality"],
    completion_criteria=[
        "process analysis complete",
        "bottlenecks identified",
        "recommendations documented",
        "report artifact created",
    ],
    failure_conditions=_DEFAULT_FAILURE_CONDITIONS,
    handoff_contract=_DEFAULT_HANDOFF,
)

operations_operations_plan_v1 = TeamExecutionContract(
    contract_id="operations.operations_plan.v1",
    team_id="operations",
    version=1,
    status=ContractStatus.ACTIVE,
    description="Produce an operational plan for a project, initiative, or ongoing function.",
    accepted_task_types=["operations_plan", "operational_plan"],
    required_inputs=[
        _text_input("initiative", "The project or initiative requiring an operational plan."),
    ],
    optional_inputs=[
        _text_input("constraints", "Resource, time, or budget constraints.", required=False),
        _text_input("stakeholders", "Key stakeholders and their roles.", required=False),
    ],
    required_skills=["workflow_planning", "task_coordination", "documentation"],
    required_tools=["task_management", "document_processing"],
    required_knowledge=["SOPs", "operations_management"],
    reasoning_profile="operational_planning",
    pipeline_id="operations_pipeline",
    output_contract_ids=["operations_plan"],
    expected_artifacts=[
        ContractArtifactExpectation(artifact_type="document", required=True, format="md", description="Operational plan document."),
    ],
    quality_gate_ids=["operations_quality"],
    completion_criteria=[
        "operations plan created",
        "all plan sections complete",
        "quality gate passed",
    ],
    failure_conditions=_DEFAULT_FAILURE_CONDITIONS,
    handoff_contract=_DEFAULT_HANDOFF,
)


# ─────────────────────────────────────────────────────────────────────────────
# Catalogue Registry — canonical list of all 21 contracts
# ─────────────────────────────────────────────────────────────────────────────

ALL_CONTRACTS = [
    # Developer
    developer_software_development_v1,
    developer_bug_fix_v1,
    developer_api_development_v1,
    # Research
    research_research_report_v1,
    research_fact_verification_v1,
    research_market_research_v1,
    # Creative
    creative_promotional_video_v1,
    creative_image_generation_v1,
    creative_creative_asset_v1,
    # Legal
    legal_legal_research_v1,
    legal_contract_analysis_v1,
    legal_contract_draft_v1,
    # Marketing
    marketing_campaign_v1,
    marketing_content_strategy_v1,
    marketing_marketing_plan_v1,
    # Finance
    finance_financial_analysis_v1,
    finance_budget_v1,
    finance_financial_report_v1,
    # Operations
    operations_workflow_execution_v1,
    operations_process_analysis_v1,
    operations_operations_plan_v1,
]


def load_contract_catalogue(registry=None):
    """
    Idempotently loads ALL_CONTRACTS into an ExecutionContractRegistry.
    If no registry is provided, returns the list directly.
    """
    if registry is None:
        return ALL_CONTRACTS

    from execution.contracts.registry import ExecutionContractRegistryError
    for contract in ALL_CONTRACTS:
        try:
            registry.register(contract)
        except ExecutionContractRegistryError:
            pass  # Already registered — idempotent
    return registry
