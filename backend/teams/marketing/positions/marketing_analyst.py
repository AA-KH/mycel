from workforce.positions.models import (
    Position, PositionStatus, PositionType, Seniority, Criticality,
    PositionSkillRequirement, PositionToolRequirement, PositionKnowledgeRequirement,
    PositionReasoningRequirement, WorkforceRequirement, Requiredness
)

marketing_analyst = Position(
    position_id="marketing_analyst",
    team_id="marketing",
    name="Marketing Analyst",
    display_name="Marketing Analyst",
    purpose="Analyze market research, build competitor profiles, define audience segments and personas, "
            "interpret campaign performance, identify growth opportunities, and create SEO strategy. "
            "Serves as the intelligence bridge between the Research Team and the Marketing Team.",
    status=PositionStatus.ACTIVE,
    position_type=PositionType.SPECIALIST,
    seniority=Seniority.SENIOR,
    criticality=Criticality.HIGH,
    workforce=WorkforceRequirement(
        min_headcount=1, max_headcount=1,
        recommended_headcount=1, requiredness=Requiredness.REQUIRED
    ),
    required_skills=[
        PositionSkillRequirement(skill_id="market_analysis", minimum_proficiency=90, required=True),
        PositionSkillRequirement(skill_id="competitive_intelligence", minimum_proficiency=90, required=True),
        PositionSkillRequirement(skill_id="audience_analysis", minimum_proficiency=85, required=True),
        PositionSkillRequirement(skill_id="data_interpretation", minimum_proficiency=90, required=True),
        PositionSkillRequirement(skill_id="seo_analysis", minimum_proficiency=80, required=True),
        PositionSkillRequirement(skill_id="marketing_analytics", minimum_proficiency=85, required=True),
        PositionSkillRequirement(skill_id="research_methodology", minimum_proficiency=80, required=True),
    ],
    required_tools=[
        PositionToolRequirement(tool_id="web.search", required=True),
    ],
    required_knowledge=[
        PositionKnowledgeRequirement(knowledge_space_id="marketing_analytics", required=True),
        PositionKnowledgeRequirement(knowledge_space_id="competitive_intelligence", required=True),
        PositionKnowledgeRequirement(knowledge_space_id="seo_methodology", required=True),
    ],
    reasoning_requirements=[
        PositionReasoningRequirement(preferred_strategy_id="marketing_strategy", required=True),
    ],
    pipeline_responsibilities=["marketing_pipeline"],
    stage_responsibilities=["research", "analyze"],
    output_responsibilities=["market_analysis", "competitor_profile", "audience_analysis", "seo_plan", "analytics_report"],
    quality_responsibilities=[],
)
