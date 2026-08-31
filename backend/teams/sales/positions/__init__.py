from workforce.positions.models import (
    Position, PositionStatus, PositionType, Seniority, Criticality,
    PositionSkillRequirement, PositionToolRequirement, PositionKnowledgeRequirement,
    PositionReasoningRequirement, WorkforceRequirement, Requiredness
)

property_advisor = Position(
    position_id="property_advisor",
    team_id="sales",
    name="Property Advisor",
    display_name="Property Advisor",
    purpose="Help customers find, compare and evaluate properties based on their requirements.",
    status=PositionStatus.ACTIVE,
    position_type=PositionType.SPECIALIST,
    seniority=Seniority.MID,
    criticality=Criticality.HIGH,
    workforce=WorkforceRequirement(
        min_headcount=1, max_headcount=20,
        recommended_headcount=5, requiredness=Requiredness.REQUIRED
    ),
    required_skills=[
        PositionSkillRequirement(skill_id="property_search", minimum_proficiency=85, required=True),
        PositionSkillRequirement(skill_id="customer_needs_analysis", minimum_proficiency=80, required=True),
        PositionSkillRequirement(skill_id="property_comparison", minimum_proficiency=75, required=True),
        PositionSkillRequirement(skill_id="multilingual_communication", minimum_proficiency=70, required=False),
    ],
    required_tools=[
        PositionToolRequirement(tool_id="property.search", required=True),
        PositionToolRequirement(tool_id="property.compare", required=True),
        PositionToolRequirement(tool_id="property.investment_analysis", required=False),
    ],
    required_knowledge=[
        PositionKnowledgeRequirement(knowledge_space_id="property_database", required=True),
        PositionKnowledgeRequirement(knowledge_space_id="local_market", required=True),
    ],
    reasoning_requirements=[
        PositionReasoningRequirement(preferred_strategy_id="customer_centric_recommendation", required=True),
    ],
    pipeline_responsibilities=["sales_pipeline"],
    stage_responsibilities=["discovery", "recommendation", "follow_up"],
    output_responsibilities=["property_shortlist"],
    quality_responsibilities=["recommendation_review"],
)
