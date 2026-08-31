from workforce.positions.models import (
    Position, PositionStatus, PositionType, Seniority, Criticality,
    PositionSkillRequirement, PositionToolRequirement, PositionKnowledgeRequirement,
    PositionReasoningRequirement, WorkforceRequirement, Requiredness
)

growth_specialist = Position(
    position_id="growth_specialist",
    team_id="marketing",
    name="Growth Specialist",
    display_name="Growth Specialist",
    purpose="Design and optimize growth systems — funnel analysis, growth loop design, "
            "acquisition strategy, conversion optimization, retention planning, and "
            "rigorous experimentation methodology. Systems thinker focused on sustainable growth.",
    status=PositionStatus.ACTIVE,
    position_type=PositionType.SPECIALIST,
    seniority=Seniority.SENIOR,
    criticality=Criticality.HIGH,
    workforce=WorkforceRequirement(
        min_headcount=1, max_headcount=1,
        recommended_headcount=1, requiredness=Requiredness.REQUIRED
    ),
    required_skills=[
        PositionSkillRequirement(skill_id="growth_hacking", minimum_proficiency=90, required=True),
        PositionSkillRequirement(skill_id="funnel_optimization", minimum_proficiency=90, required=True),
        PositionSkillRequirement(skill_id="experiment_design", minimum_proficiency=85, required=True),
        PositionSkillRequirement(skill_id="conversion_optimization", minimum_proficiency=85, required=True),
        PositionSkillRequirement(skill_id="unit_economics", minimum_proficiency=80, required=True),
        PositionSkillRequirement(skill_id="retention_analysis", minimum_proficiency=80, required=True),
        PositionSkillRequirement(skill_id="statistical_reasoning", minimum_proficiency=75, required=True),
    ],
    required_tools=[
        PositionToolRequirement(tool_id="web.search", required=True),
    ],
    required_knowledge=[
        PositionKnowledgeRequirement(knowledge_space_id="growth_methodology", required=True),
        PositionKnowledgeRequirement(knowledge_space_id="experimentation", required=True),
        PositionKnowledgeRequirement(knowledge_space_id="unit_economics", required=True),
    ],
    reasoning_requirements=[
        PositionReasoningRequirement(preferred_strategy_id="marketing_strategy", required=True),
    ],
    pipeline_responsibilities=["marketing_pipeline"],
    stage_responsibilities=["growth"],
    output_responsibilities=["growth_plan", "growth_experiment", "funnel_analysis"],
    quality_responsibilities=[],
)
