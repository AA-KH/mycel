from workforce.positions.models import (
    Position, PositionStatus, PositionType, Seniority, Criticality,
    PositionSkillRequirement, PositionToolRequirement, PositionKnowledgeRequirement,
    PositionReasoningRequirement, WorkforceRequirement, Requiredness
)

compliance_analyst = Position(
    position_id="compliance_analyst",
    team_id="legal",
    name="Compliance Analyst",
    display_name="Compliance Analyst",
    purpose="Ensure corporate activities adhere to regulatory compliance standards.",
    status=PositionStatus.ACTIVE,
    position_type=PositionType.SPECIALIST,
    seniority=Seniority.MID,
    criticality=Criticality.HIGH,
    workforce=WorkforceRequirement(
        min_headcount=1, max_headcount=5,
        recommended_headcount=2, requiredness=Requiredness.REQUIRED
    ),
    required_skills=[
        PositionSkillRequirement(skill_id="compliance_analysis", minimum_proficiency=85, required=True),
        PositionSkillRequirement(skill_id="document_analysis", minimum_proficiency=75, required=True),
        PositionSkillRequirement(skill_id="legal_research", minimum_proficiency=70, required=True),
        PositionSkillRequirement(skill_id="legal_writing", minimum_proficiency=65, required=True),
        PositionSkillRequirement(skill_id="contract_analysis", minimum_proficiency=50, required=False),
        PositionSkillRequirement(skill_id="citation_validation", minimum_proficiency=50, required=False),
    ],
    required_tools=[
        PositionToolRequirement(tool_id="document_search", required=True),
        PositionToolRequirement(tool_id="rag_retrieval", required=True),
        PositionToolRequirement(tool_id="legal_document_parser", required=True),
        PositionToolRequirement(tool_id="document_generation", required=True),
        PositionToolRequirement(tool_id="citation_tools", required=False),
    ],
    required_knowledge=[
        PositionKnowledgeRequirement(knowledge_space_id="indian_regulations", required=True),
        PositionKnowledgeRequirement(knowledge_space_id="indian_statutes", required=True),
        PositionKnowledgeRequirement(knowledge_space_id="indian_legal_system", required=True),
        PositionKnowledgeRequirement(knowledge_space_id="legal_terminology", required=True),
    ],
    reasoning_requirements=[
        PositionReasoningRequirement(preferred_strategy_id="compliance_risk_assessment", required=True),
    ],
    pipeline_responsibilities=["legal_pipeline"],
    stage_responsibilities=["compliance_check", "risk_assessment"],
    output_responsibilities=["compliance_report"],
    quality_responsibilities=["compliance_review"],
)
