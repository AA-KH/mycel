from workforce.positions.models import (
    Position, PositionStatus, PositionType, Seniority, Criticality,
    PositionSkillRequirement, PositionToolRequirement, PositionKnowledgeRequirement,
    PositionReasoningRequirement, WorkforceRequirement, Requiredness
)

content_creator = Position(
    position_id="content_creator",
    team_id="marketing",
    name="Content Creator",
    display_name="Content Creator",
    purpose="Produce channel-native marketing content across all platforms — social media, blog, email, "
            "landing pages, ad copy, and more. Maintain brand voice consistency, ensure platform fitness, "
            "and create content calendars aligned with marketing strategy.",
    status=PositionStatus.ACTIVE,
    position_type=PositionType.INDIVIDUAL_CONTRIBUTOR,
    seniority=Seniority.SENIOR,
    criticality=Criticality.HIGH,
    workforce=WorkforceRequirement(
        min_headcount=1, max_headcount=2,
        recommended_headcount=1, requiredness=Requiredness.REQUIRED
    ),
    required_skills=[
        PositionSkillRequirement(skill_id="copywriting", minimum_proficiency=90, required=True),
        PositionSkillRequirement(skill_id="content_creation", minimum_proficiency=90, required=True),
        PositionSkillRequirement(skill_id="social_media_marketing", minimum_proficiency=85, required=True),
        PositionSkillRequirement(skill_id="email_marketing", minimum_proficiency=80, required=True),
        PositionSkillRequirement(skill_id="seo_writing", minimum_proficiency=75, required=True),
        PositionSkillRequirement(skill_id="brand_voice", minimum_proficiency=85, required=True),
        PositionSkillRequirement(skill_id="content_strategy", minimum_proficiency=80, required=True),
    ],
    required_tools=[
        PositionToolRequirement(tool_id="web.search", required=True),
    ],
    required_knowledge=[
        PositionKnowledgeRequirement(knowledge_space_id="content_marketing", required=True),
        PositionKnowledgeRequirement(knowledge_space_id="social_media_platforms", required=True),
        PositionKnowledgeRequirement(knowledge_space_id="email_marketing", required=True),
    ],
    reasoning_requirements=[
        PositionReasoningRequirement(preferred_strategy_id="marketing_strategy", required=True),
    ],
    pipeline_responsibilities=["marketing_pipeline"],
    stage_responsibilities=["create"],
    output_responsibilities=["content_asset", "content_calendar", "email_campaign", "social_post"],
    quality_responsibilities=[],
)
