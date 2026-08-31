"""
Team Collaboration Contract Catalogue (TOS 19)

Defines the intentional initial collaboration relationships between
Mycel's 7 core teams.

Collaboration matrix:
    Research  → Developer      (provide verified requirements)
    Research  → Marketing      (provide market analysis)
    Developer → Creative       (provide product context for production)
    Creative  → Marketing      (provide finished creative assets)
    Legal     → Marketing      (provide compliance review)
    Finance   → Operations     (provide approved budget)
    Operations → Developer     (provide workflow & process requirements)

Design principle:
    - Only meaningful business dependencies are modelled.
    - No combinatorial explosion (not every team to every team).
    - Each contract references the providing team's existing Execution Contract
      and Pipeline IDs.

NO execution occurs here — this is pure contract definition.
"""

from execution.collaboration.models import (
    TeamCollaborationContract,
    CollaborationStatus,
    CollaborationSequenceType,
    CollaborationFailureCondition,
    CollaborationConstraints,
    CollaborationHandoffContract,
)
from execution.contracts.models import ContractInputField, ContractInputType


# ─────────────────────────────────────────────────────────────────────────────
# Shared helpers
# ─────────────────────────────────────────────────────────────────────────────

_DEFAULT_FAILURE_CONDITIONS = [
    CollaborationFailureCondition.INPUT_INVALID,
    CollaborationFailureCondition.CAPABILITY_UNAVAILABLE,
    CollaborationFailureCondition.PROVIDER_UNAVAILABLE,
    CollaborationFailureCondition.PIPELINE_UNAVAILABLE,
    CollaborationFailureCondition.OUTPUT_MISSING,
    CollaborationFailureCondition.QUALITY_FAILED,
]

_DEFAULT_HANDOFF = CollaborationHandoffContract()
_DEFAULT_CONSTRAINTS = CollaborationConstraints()


def _text(input_id: str, description: str, required: bool = True) -> ContractInputField:
    return ContractInputField(
        input_id=input_id,
        type=ContractInputType.TEXT,
        description=description,
        required=required,
    )


def _doc(input_id: str, description: str, required: bool = True) -> ContractInputField:
    return ContractInputField(
        input_id=input_id,
        type=ContractInputType.DOCUMENT,
        description=description,
        required=required,
    )


def _artifact(input_id: str, description: str, required: bool = True) -> ContractInputField:
    return ContractInputField(
        input_id=input_id,
        type=ContractInputType.ARTIFACT_REFERENCE,
        description=description,
        required=required,
    )


# ─────────────────────────────────────────────────────────────────────────────
# 1. Research → Developer
#    Purpose: Research team provides verified requirements for Developer implementation.
# ─────────────────────────────────────────────────────────────────────────────

research_to_developer_requirements_v1 = TeamCollaborationContract(
    contract_id="research_to_developer.requirements.v1",
    version=1,
    status=CollaborationStatus.ACTIVE,
    purpose=(
        "The Research team provides verified product and market requirements "
        "to the Developer team for implementation planning and feature development."
    ),
    requesting_team_id="developer",
    providing_team_id="research",
    request_type="requirements",
    accepted_request_types=["requirements", "research_report", "market_research"],
    required_inputs=[
        _text("product_description", "Description of the product or feature to research."),
        _text("research_scope", "Scope and focus areas for the research."),
    ],
    optional_inputs=[
        _text("target_market", "Target market or customer segment.", required=False),
        _text("competitor_context", "Known competitors or market alternatives.", required=False),
    ],
    required_capabilities=["research", "synthesis", "information_retrieval"],
    required_tools=["web_search", "document_parsing"],
    required_knowledge=["research_methodology"],
    required_reasoning="research_verify",
    execution_contract_id="research.research_report.v1",
    pipeline_id="research_pipeline",
    required_output_contract_ids=["research_report"],
    quality_gate_ids=["source_quality", "completeness"],
    sequence_type=CollaborationSequenceType.SEQUENTIAL,
    completion_criteria=[
        "research complete",
        "requirements document artifact created",
        "sources verified",
        "quality gates passed",
        "ArtifactReference handed to Developer team",
    ],
    failure_conditions=_DEFAULT_FAILURE_CONDITIONS,
    collaboration_constraints=CollaborationConstraints(
        max_round_trips=2,
        requires_quality_pass=True,
        partial_output_allowed=True,
    ),
    handoff_contract=CollaborationHandoffContract(include_source_references=True),
)


# ─────────────────────────────────────────────────────────────────────────────
# 2. Research → Marketing
#    Purpose: Research team provides market analysis for campaign planning.
# ─────────────────────────────────────────────────────────────────────────────

research_to_marketing_market_analysis_v1 = TeamCollaborationContract(
    contract_id="research_to_marketing.market_analysis.v1",
    version=1,
    status=CollaborationStatus.ACTIVE,
    purpose=(
        "The Research team provides market analysis, audience profiling, "
        "and competitor intelligence to the Marketing team for campaign and "
        "content strategy development."
    ),
    requesting_team_id="marketing",
    providing_team_id="research",
    request_type="market_analysis",
    accepted_request_types=["market_analysis", "market_research", "audience_research"],
    required_inputs=[
        _text("research_scope", "Market, industry, or audience segment to research."),
        _text("product_context", "The product or service context for the analysis."),
    ],
    optional_inputs=[
        _text("focus_areas", "Specific focus: competitors, trends, sizing, audience.", required=False),
        _text("geography", "Target geographic market.", required=False),
    ],
    required_capabilities=["research", "data_analysis", "synthesis"],
    required_tools=["web_search", "data_extraction"],
    required_knowledge=["research_methodology"],
    required_reasoning="research_verify",
    execution_contract_id="research.market_research.v1",
    pipeline_id="research_pipeline",
    required_output_contract_ids=["market_research_report"],
    quality_gate_ids=["source_quality", "completeness"],
    sequence_type=CollaborationSequenceType.SEQUENTIAL,
    completion_criteria=[
        "market analysis report created",
        "audience profile documented",
        "competitor analysis included",
        "quality gates passed",
        "ArtifactReference handed to Marketing team",
    ],
    failure_conditions=_DEFAULT_FAILURE_CONDITIONS,
    collaboration_constraints=CollaborationConstraints(
        max_round_trips=1,
        requires_quality_pass=True,
    ),
    handoff_contract=CollaborationHandoffContract(include_source_references=True),
)


# ─────────────────────────────────────────────────────────────────────────────
# 3. Developer → Creative
#    Purpose: Developer provides product context for creative production.
# ─────────────────────────────────────────────────────────────────────────────

developer_to_creative_product_demo_v1 = TeamCollaborationContract(
    contract_id="developer_to_creative.product_demo.v1",
    version=1,
    status=CollaborationStatus.ACTIVE,
    purpose=(
        "The Developer team provides product descriptions, feature summaries, "
        "and technical context to the Creative team for producing promotional "
        "and marketing creative assets."
    ),
    requesting_team_id="creative",
    providing_team_id="developer",
    request_type="product_demo",
    accepted_request_types=["product_demo", "product_context", "feature_summary"],
    required_inputs=[
        _text("product_description", "Description of the product to be showcased."),
        _text("feature_list", "Key features and capabilities to highlight."),
    ],
    optional_inputs=[
        _artifact("ui_screenshots", "UI screenshots or design references.", required=False),
        _text("brand_guidelines", "Brand guidelines or visual style references.", required=False),
    ],
    required_capabilities=["programming", "software_engineering", "documentation"],
    required_tools=["git", "terminal"],
    required_knowledge=["software_engineering"],
    required_reasoning="engineering_reasoning",
    execution_contract_id="developer.software_development.v1",
    pipeline_id="development_pipeline",
    required_output_contract_ids=["source_code"],
    quality_gate_ids=["code_quality"],
    sequence_type=CollaborationSequenceType.SEQUENTIAL,
    completion_criteria=[
        "product context document produced",
        "feature summary included",
        "technical accuracy validated",
        "ArtifactReference handed to Creative team",
    ],
    failure_conditions=_DEFAULT_FAILURE_CONDITIONS,
    collaboration_constraints=_DEFAULT_CONSTRAINTS,
    handoff_contract=_DEFAULT_HANDOFF,
)


# ─────────────────────────────────────────────────────────────────────────────
# 4. Creative → Marketing
#    Purpose: Creative team delivers finished assets for distribution.
# ─────────────────────────────────────────────────────────────────────────────

creative_to_marketing_promotional_asset_v1 = TeamCollaborationContract(
    contract_id="creative_to_marketing.promotional_asset.v1",
    version=1,
    status=CollaborationStatus.ACTIVE,
    purpose=(
        "The Creative team delivers production-ready promotional videos, images, "
        "and marketing assets to the Marketing team for campaign distribution."
    ),
    requesting_team_id="marketing",
    providing_team_id="creative",
    request_type="promotional_asset",
    accepted_request_types=["promotional_asset", "promotional_video", "social_media_asset", "creative_asset"],
    required_inputs=[
        _text("creative_brief", "Brief describing the required creative asset."),
        _text("target_audience", "Target audience for the asset."),
    ],
    optional_inputs=[
        _artifact("brand_assets", "Existing brand assets or guidelines.", required=False),
        _text("format_requirements", "Required output formats or dimensions.", required=False),
    ],
    required_capabilities=["creative_ideation", "storytelling", "video_editing"],
    required_tools=["video_generation", "video_editing", "image_generation"],
    required_knowledge=["visual_communication"],
    required_reasoning="creative_review",
    execution_contract_id="creative.promotional_video.v1",
    pipeline_id="creative_pipeline",
    required_output_contract_ids=["promotional_video"],
    quality_gate_ids=["visual_quality", "format_validation", "brand_consistency"],
    sequence_type=CollaborationSequenceType.SEQUENTIAL,
    completion_criteria=[
        "creative asset produced",
        "visual quality gate passed",
        "format validation passed",
        "brand consistency validated",
        "ArtifactReference handed to Marketing team",
    ],
    failure_conditions=[
        CollaborationFailureCondition.INPUT_INVALID,
        CollaborationFailureCondition.CAPABILITY_UNAVAILABLE,
        CollaborationFailureCondition.PROVIDER_UNAVAILABLE,
        CollaborationFailureCondition.PIPELINE_UNAVAILABLE,
        CollaborationFailureCondition.OUTPUT_MISSING,
        CollaborationFailureCondition.QUALITY_FAILED,
        CollaborationFailureCondition.ARTIFACT_INVALID,
    ],
    collaboration_constraints=CollaborationConstraints(
        max_round_trips=2,
        requires_quality_pass=True,
        allowed_output_types=["video", "image"],
        partial_output_allowed=False,
    ),
    handoff_contract=CollaborationHandoffContract(
        include_artifacts=True,
        include_quality_results=True,
    ),
)


# ─────────────────────────────────────────────────────────────────────────────
# 5. Legal → Marketing
#    Purpose: Legal reviews marketing content for compliance.
# ─────────────────────────────────────────────────────────────────────────────

legal_to_marketing_compliance_review_v1 = TeamCollaborationContract(
    contract_id="legal_to_marketing.compliance_review.v1",
    version=1,
    status=CollaborationStatus.ACTIVE,
    purpose=(
        "The Legal team reviews marketing campaigns and content for legal "
        "compliance under applicable Indian law and returns an approved version "
        "with a compliance report."
    ),
    requesting_team_id="marketing",
    providing_team_id="legal",
    request_type="compliance_review",
    accepted_request_types=["compliance_review", "legal_review", "content_review"],
    required_inputs=[
        _doc("marketing_content", "Marketing content, copy, or campaign materials to review."),
        _text("campaign_details", "Overview of the campaign and its objectives."),
    ],
    optional_inputs=[
        _text("jurisdiction", "Specific Indian jurisdiction if relevant.", required=False),
        _text("known_risks", "Known compliance risks or concerns to check.", required=False),
    ],
    required_capabilities=["legal_document_analysis", "legal_research", "legal_writing"],
    required_tools=["legal_document_parser"],
    required_knowledge=["indian_legal_system", "indian_statutes"],
    required_reasoning="legal_authority_verification",
    execution_contract_id="legal.contract_analysis.v1",
    pipeline_id="legal_pipeline",
    required_output_contract_ids=["contract_analysis_report"],
    quality_gate_ids=["legal_citation_quality"],
    sequence_type=CollaborationSequenceType.SEQUENTIAL,
    completion_criteria=[
        "legal review completed",
        "compliance report created",
        "all citations verified",
        "human approval obtained",
        "approved content or rejection decision handed to Marketing",
    ],
    failure_conditions=[
        CollaborationFailureCondition.INPUT_INVALID,
        CollaborationFailureCondition.CAPABILITY_UNAVAILABLE,
        CollaborationFailureCondition.PROVIDER_UNAVAILABLE,
        CollaborationFailureCondition.PIPELINE_UNAVAILABLE,
        CollaborationFailureCondition.OUTPUT_MISSING,
        CollaborationFailureCondition.QUALITY_FAILED,
        CollaborationFailureCondition.APPROVAL_REQUIRED,
    ],
    collaboration_constraints=CollaborationConstraints(
        max_round_trips=2,
        requires_human_approval=True,
        requires_quality_pass=True,
        partial_output_allowed=False,
    ),
    handoff_contract=CollaborationHandoffContract(
        include_quality_results=True,
        notes="Compliance report must be included in handoff.",
    ),
)


# ─────────────────────────────────────────────────────────────────────────────
# 6. Finance → Operations
#    Purpose: Finance provides approved budget for operational planning.
# ─────────────────────────────────────────────────────────────────────────────

finance_to_operations_budget_approval_v1 = TeamCollaborationContract(
    contract_id="finance_to_operations.budget_approval.v1",
    version=1,
    status=CollaborationStatus.ACTIVE,
    purpose=(
        "The Finance team validates and approves budget requests from the "
        "Operations team, providing financial constraints and approved spend "
        "allocations for operational planning."
    ),
    requesting_team_id="operations",
    providing_team_id="finance",
    request_type="budget_approval",
    accepted_request_types=["budget_approval", "financial_validation", "budget_review"],
    required_inputs=[
        _text("budget_request", "Budget request with line items and justifications."),
        _text("cost_estimate", "Estimated costs for the operational initiative."),
    ],
    optional_inputs=[
        _text("project_scope", "Scope of the operational initiative requiring budget.", required=False),
        _text("timeline", "Expected timeline and spend distribution.", required=False),
    ],
    required_capabilities=["financial_analysis", "budgeting", "reporting"],
    required_tools=["spreadsheet_processing", "financial_calculator"],
    required_knowledge=["budgeting", "financial_analysis"],
    required_reasoning="financial_validation",
    execution_contract_id="finance.budget.v1",
    pipeline_id="finance_pipeline",
    required_output_contract_ids=["budget_document"],
    quality_gate_ids=["financial_accuracy"],
    sequence_type=CollaborationSequenceType.SEQUENTIAL,
    completion_criteria=[
        "budget analysis complete",
        "approved budget document created",
        "financial accuracy gate passed",
        "budget constraints documented",
        "handoff to Operations ready",
    ],
    failure_conditions=_DEFAULT_FAILURE_CONDITIONS,
    collaboration_constraints=CollaborationConstraints(
        max_round_trips=2,
        requires_quality_pass=True,
    ),
    handoff_contract=_DEFAULT_HANDOFF,
)


# ─────────────────────────────────────────────────────────────────────────────
# 7. Operations → Developer
#    Purpose: Operations provides workflow and process requirements for systems.
# ─────────────────────────────────────────────────────────────────────────────

operations_to_developer_workflow_requirements_v1 = TeamCollaborationContract(
    contract_id="operations_to_developer.workflow_requirements.v1",
    version=1,
    status=CollaborationStatus.ACTIVE,
    purpose=(
        "The Operations team provides workflow definitions, process requirements, "
        "and operational constraints to the Developer team for implementing "
        "automation, tooling, or process-supporting systems."
    ),
    requesting_team_id="developer",
    providing_team_id="operations",
    request_type="workflow_requirements",
    accepted_request_types=["workflow_requirements", "process_requirements", "operations_specification"],
    required_inputs=[
        _text("workflow_description", "Description of the workflow or process to be implemented."),
        _text("system_context", "Existing systems or constraints the Developer must integrate with."),
    ],
    optional_inputs=[
        _text("performance_requirements", "Expected throughput, latency, or SLA requirements.", required=False),
        _text("edge_cases", "Known edge cases or exception paths.", required=False),
    ],
    required_capabilities=["process_management", "workflow_planning", "documentation"],
    required_tools=["task_management", "document_processing"],
    required_knowledge=["operations_management", "workflow_management"],
    required_reasoning="operational_planning",
    execution_contract_id="operations.workflow_execution.v1",
    pipeline_id="operations_pipeline",
    required_output_contract_ids=["workflow_execution_report"],
    quality_gate_ids=["operations_quality"],
    sequence_type=CollaborationSequenceType.SEQUENTIAL,
    completion_criteria=[
        "workflow requirements document created",
        "all process steps documented",
        "quality gate passed",
        "ArtifactReference handed to Developer team",
    ],
    failure_conditions=_DEFAULT_FAILURE_CONDITIONS,
    collaboration_constraints=CollaborationConstraints(
        max_round_trips=2,
        requires_quality_pass=True,
        partial_output_allowed=True,
    ),
    handoff_contract=_DEFAULT_HANDOFF,
)


# ─────────────────────────────────────────────────────────────────────────────
# Canonical catalogue — all 7 intentional collaboration contracts
# ─────────────────────────────────────────────────────────────────────────────

ALL_COLLABORATION_CONTRACTS = [
    research_to_developer_requirements_v1,
    research_to_marketing_market_analysis_v1,
    developer_to_creative_product_demo_v1,
    creative_to_marketing_promotional_asset_v1,
    legal_to_marketing_compliance_review_v1,
    finance_to_operations_budget_approval_v1,
    operations_to_developer_workflow_requirements_v1,
]


def load_collaboration_catalogue(registry=None):
    """
    Idempotently loads ALL_COLLABORATION_CONTRACTS into a
    TeamCollaborationContractRegistry. If no registry is provided,
    returns the list directly.
    """
    if registry is None:
        return ALL_COLLABORATION_CONTRACTS

    from execution.collaboration.registry import CollaborationContractRegistryError
    for contract in ALL_COLLABORATION_CONTRACTS:
        try:
            registry.register(contract)
        except CollaborationContractRegistryError:
            pass  # Already registered — idempotent
    return registry
