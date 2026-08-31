from workforce.positions.models import (
    Position, PositionStatus, PositionType, Seniority, Criticality,
    PositionSkillRequirement, PositionToolRequirement, PositionKnowledgeRequirement,
    PositionReasoningRequirement, WorkforceRequirement, Requiredness
)

legal_researcher = Position(
    position_id="legal_researcher",
    team_id="legal",
    name="Legal Researcher",
    display_name="Legal Researcher",
    purpose="Conduct comprehensive legal research and gather authoritative legal precedents.",
    status=PositionStatus.ACTIVE,
    position_type=PositionType.SPECIALIST,
    seniority=Seniority.MID,
    criticality=Criticality.HIGH,
    workforce=WorkforceRequirement(
        min_headcount=1, max_headcount=8,
        recommended_headcount=2, requiredness=Requiredness.REQUIRED
    ),
    required_skills=[
        PositionSkillRequirement(skill_id="legal_research", minimum_proficiency=90, required=True),
        PositionSkillRequirement(skill_id="document_analysis", minimum_proficiency=80, required=True),
        PositionSkillRequirement(skill_id="citation_validation", minimum_proficiency=85, required=True),
        PositionSkillRequirement(skill_id="legal_writing", minimum_proficiency=60, required=False),
        PositionSkillRequirement(skill_id="contract_analysis", minimum_proficiency=40, required=False),
        PositionSkillRequirement(skill_id="compliance_analysis", minimum_proficiency=50, required=False),
    ],
    required_tools=[
        PositionToolRequirement(tool_id="rag_retrieval", required=True),
        PositionToolRequirement(tool_id="document_search", required=True),
        PositionToolRequirement(tool_id="citation_tools", required=True),
        PositionToolRequirement(tool_id="legal_document_parser", required=True),
        PositionToolRequirement(tool_id="document_generation", required=False),
    ],
    required_knowledge=[
        PositionKnowledgeRequirement(knowledge_space_id="indian_case_law", required=True),
        PositionKnowledgeRequirement(knowledge_space_id="indian_statutes", required=True),
        PositionKnowledgeRequirement(knowledge_space_id="indian_legal_system", required=True),
        PositionKnowledgeRequirement(knowledge_space_id="legal_terminology", required=True),
    ],
    reasoning_requirements=[
        PositionReasoningRequirement(preferred_strategy_id="legal_authority_verification", required=True),
    ],
    pipeline_responsibilities=["legal_pipeline"],
    stage_responsibilities=["research", "verification"],
    output_responsibilities=["legal_research_report"],
    quality_responsibilities=["citation_validation"],
)
