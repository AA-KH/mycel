from workforce.positions.models import (
    Position, PositionStatus, PositionType, Seniority, Criticality,
    PositionSkillRequirement, PositionToolRequirement, PositionKnowledgeRequirement,
    PositionReasoningRequirement, WorkforceRequirement, Requiredness
)

accounts_specialist = Position(
    position_id="accounts_specialist",
    team_id="finance",
    name="Accounts Specialist",
    display_name="Accounts Specialist",
    purpose="Manage accounts payable/receivable, reconcile financial statements, and ensure accurate financial record-keeping.",
    status=PositionStatus.ACTIVE,
    position_type=PositionType.INDIVIDUAL_CONTRIBUTOR,
    seniority=Seniority.MID,
    criticality=Criticality.HIGH,
    workforce=WorkforceRequirement(
        min_headcount=1, max_headcount=5,
        recommended_headcount=2, requiredness=Requiredness.REQUIRED
    ),
    required_skills=[
        PositionSkillRequirement(skill_id="accounting", minimum_proficiency=80, required=True),
        PositionSkillRequirement(skill_id="reconciliation", minimum_proficiency=75, required=True),
        PositionSkillRequirement(skill_id="financial_reporting", minimum_proficiency=70, required=True),
        PositionSkillRequirement(skill_id="compliance", minimum_proficiency=65, required=True),
        PositionSkillRequirement(skill_id="data_analysis", minimum_proficiency=60, required=False),
        PositionSkillRequirement(skill_id="cost_analysis", minimum_proficiency=55, required=False),
    ],
    required_tools=[
        PositionToolRequirement(tool_id="spreadsheet.processing", required=True),
        PositionToolRequirement(tool_id="financial.calculator", required=True),
        PositionToolRequirement(tool_id="document.generation", required=True),
        PositionToolRequirement(tool_id="database.query", required=False),
    ],
    required_knowledge=[
        PositionKnowledgeRequirement(knowledge_space_id="accounting_fundamentals", required=True),
        PositionKnowledgeRequirement(knowledge_space_id="financial_reporting_standards", required=True),
        PositionKnowledgeRequirement(knowledge_space_id="regulatory_compliance", required=True),
        PositionKnowledgeRequirement(knowledge_space_id="audit_procedures", required=False),
    ],
    reasoning_requirements=[
        PositionReasoningRequirement(preferred_strategy_id="financial_validation", required=True),
    ],
    pipeline_responsibilities=["accounts_pipeline"],
    stage_responsibilities=["recording", "reconciliation", "reporting"],
    output_responsibilities=["reconciliation_report", "financial_statement"],
    quality_responsibilities=["accuracy_check", "compliance_review"],
)
