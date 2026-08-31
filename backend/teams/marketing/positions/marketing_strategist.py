from workforce.positions.models import (
    Position, PositionStatus, PositionType, Seniority, Criticality,
    PositionSkillRequirement, PositionToolRequirement, PositionKnowledgeRequirement,
    PositionReasoningRequirement, WorkforceRequirement, Requiredness
)

marketing_strategist = Position(
    position_id="marketing_strategist",
    team_id="marketing",
    name="Marketing Strategist",
    display_name="Marketing Strategist",
    purpose="Lead strategic marketing direction — translate business objectives into marketing strategy, "
            "define positioning, messaging, audience, channel selection, and campaign architecture. "
            "Coordinate the Marketing Team and ensure strategic coherence across all outputs.",
    status=PositionStatus.ACTIVE,
    position_type=PositionType.LEADERSHIP,
    seniority=Seniority.SENIOR,
    criticality=Criticality.CRITICAL,
    workforce=WorkforceRequirement(
        min_headcount=1, max_headcount=1,
        recommended_headcount=1, requiredness=Requiredness.REQUIRED
    ),
    required_skills=[
        PositionSkillRequirement(skill_id="marketing_strategy", minimum_proficiency=95, required=True),
        PositionSkillRequirement(skill_id="brand_positioning", minimum_proficiency=90, required=True),
        PositionSkillRequirement(skill_id="audience_analysis", minimum_proficiency=90, required=True),
        PositionSkillRequirement(skill_id="messaging_architecture", minimum_proficiency=90, required=True),
        PositionSkillRequirement(skill_id="channel_strategy", minimum_proficiency=85, required=True),
        PositionSkillRequirement(skill_id="campaign_planning", minimum_proficiency=85, required=True),
        PositionSkillRequirement(skill_id="competitive_analysis", minimum_proficiency=80, required=True),
        PositionSkillRequirement(skill_id="business_acumen", minimum_proficiency=85, required=True),
        PositionSkillRequirement(skill_id="communication", minimum_proficiency=90, required=True),
    ],
    required_tools=[
        PositionToolRequirement(tool_id="web.search", required=True),
    ],
    required_knowledge=[
        PositionKnowledgeRequirement(knowledge_space_id="marketing_strategy", required=True),
        PositionKnowledgeRequirement(knowledge_space_id="brand_management", required=True),
        PositionKnowledgeRequirement(knowledge_space_id="digital_marketing", required=True),
        PositionKnowledgeRequirement(knowledge_space_id="consumer_behavior", required=True),
    ],
    reasoning_requirements=[
        PositionReasoningRequirement(preferred_strategy_id="marketing_strategy", required=True),
    ],
    pipeline_responsibilities=["marketing_pipeline"],
    stage_responsibilities=["classify", "brief", "strategize", "quality", "synthesize"],
    output_responsibilities=["marketing_strategy", "marketing_brief", "campaign", "creative_brief", "marketing_artifact"],
    quality_responsibilities=["marketing_quality_gate"],
)
