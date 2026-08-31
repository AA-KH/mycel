from workforce.positions.models import (
    Position, PositionStatus, PositionType, Seniority, Criticality,
    PositionSkillRequirement, PositionToolRequirement, PositionKnowledgeRequirement,
    PositionReasoningRequirement, WorkforceRequirement, Requiredness
)

senior_lawyer = Position(
    position_id="senior_lawyer",
    team_id="legal",
    name="Senior Lawyer",
    display_name="Senior Lawyer",
    purpose="Lead legal strategy, provide expert legal advice, and oversee complex legal matters.",
    status=PositionStatus.ACTIVE,
    position_type=PositionType.LEADERSHIP,
    seniority=Seniority.SENIOR,
    criticality=Criticality.HIGH,
    workforce=WorkforceRequirement(
        min_headcount=1, max_headcount=3,
        recommended_headcount=1, requiredness=Requiredness.REQUIRED
    ),
    required_skills=[
        PositionSkillRequirement(skill_id="legal_research", minimum_proficiency=85, required=True),
        PositionSkillRequirement(skill_id="document_analysis", minimum_proficiency=90, required=True),
        PositionSkillRequirement(skill_id="contract_analysis", minimum_proficiency=85, required=True),
        PositionSkillRequirement(skill_id="compliance_analysis", minimum_proficiency=80, required=True),
        PositionSkillRequirement(skill_id="legal_writing", minimum_proficiency=85, required=True),
        PositionSkillRequirement(skill_id="citation_validation", minimum_proficiency=80, required=True),
    ],
    required_tools=[
        PositionToolRequirement(tool_id="legal_document_parser", required=True),
        PositionToolRequirement(tool_id="rag_retrieval", required=True),
        PositionToolRequirement(tool_id="document_search", required=True),
        PositionToolRequirement(tool_id="citation_tools", required=True),
        PositionToolRequirement(tool_id="document_generation", required=True),
    ],
    required_knowledge=[
        PositionKnowledgeRequirement(knowledge_space_id="indian_legal_system", required=True),
        PositionKnowledgeRequirement(knowledge_space_id="indian_statutes", required=True),
        PositionKnowledgeRequirement(knowledge_space_id="indian_regulations", required=True),
        PositionKnowledgeRequirement(knowledge_space_id="indian_case_law", required=True),
        PositionKnowledgeRequirement(knowledge_space_id="legal_terminology", required=True),
    ],
    reasoning_requirements=[
        PositionReasoningRequirement(preferred_strategy_id="legal_authority_verification", required=True),
        PositionReasoningRequirement(preferred_strategy_id="compliance_risk_assessment", required=False),
    ],
    pipeline_responsibilities=["legal_pipeline"],
    stage_responsibilities=["strategy", "advisory", "final_review"],
    output_responsibilities=["legal_opinion", "strategy_document"],
    quality_responsibilities=["legal_oversight"],
)
