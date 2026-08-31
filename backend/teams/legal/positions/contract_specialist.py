from workforce.positions.models import (
    Position, PositionStatus, PositionType, Seniority, Criticality,
    PositionSkillRequirement, PositionToolRequirement, PositionKnowledgeRequirement,
    PositionReasoningRequirement, WorkforceRequirement, Requiredness
)

contract_specialist = Position(
    position_id="contract_specialist",
    team_id="legal",
    name="Contract Specialist",
    display_name="Contract Specialist",
    purpose="Draft, review, and manage contracts with focus on legal and business compliance.",
    status=PositionStatus.ACTIVE,
    position_type=PositionType.SPECIALIST,
    seniority=Seniority.MID,
    criticality=Criticality.HIGH,
    workforce=WorkforceRequirement(
        min_headcount=1, max_headcount=8,
        recommended_headcount=2, requiredness=Requiredness.REQUIRED
    ),
    required_skills=[
        PositionSkillRequirement(skill_id="contract_analysis", minimum_proficiency=85, required=True),
        PositionSkillRequirement(skill_id="legal_writing", minimum_proficiency=80, required=True),
        PositionSkillRequirement(skill_id="document_analysis", minimum_proficiency=75, required=True),
        PositionSkillRequirement(skill_id="compliance_analysis", minimum_proficiency=70, required=True),
        PositionSkillRequirement(skill_id="legal_research", minimum_proficiency=60, required=False),
        PositionSkillRequirement(skill_id="citation_validation", minimum_proficiency=50, required=False),
    ],
    required_tools=[
        PositionToolRequirement(tool_id="legal_document_parser", required=True),
        PositionToolRequirement(tool_id="document_generation", required=True),
        PositionToolRequirement(tool_id="document_search", required=True),
        PositionToolRequirement(tool_id="rag_retrieval", required=False),
    ],
    required_knowledge=[
        PositionKnowledgeRequirement(knowledge_space_id="indian_statutes", required=True),
        PositionKnowledgeRequirement(knowledge_space_id="indian_regulations", required=True),
        PositionKnowledgeRequirement(knowledge_space_id="legal_terminology", required=True),
        PositionKnowledgeRequirement(knowledge_space_id="indian_case_law", required=False),
    ],
    reasoning_requirements=[
        PositionReasoningRequirement(preferred_strategy_id="legal_authority_verification", required=False),
    ],
    pipeline_responsibilities=["legal_pipeline"],
    stage_responsibilities=["drafting", "review"],
    output_responsibilities=["contract_document"],
    quality_responsibilities=["contract_review"],
)
