from workforce.positions.models import (
    Position, PositionStatus, PositionType, Seniority, Criticality,
    PositionSkillRequirement, PositionToolRequirement, PositionKnowledgeRequirement,
    PositionReasoningRequirement, WorkforceRequirement, Requiredness
)

creative_strategist = Position(
    position_id="creative_strategist",
    team_id="creative",
    name="Creative Strategist",
    display_name="Creative Strategist",
    purpose="Define brand direction and conceptualize marketing campaigns.",
    status=PositionStatus.ACTIVE,
    position_type=PositionType.LEADERSHIP,
    seniority=Seniority.SENIOR,
    criticality=Criticality.HIGH,
    workforce=WorkforceRequirement(min_headcount=1, max_headcount=5, recommended_headcount=2, requiredness=Requiredness.REQUIRED),
    required_skills=[PositionSkillRequirement(skill_id="creative_direction", minimum_proficiency=70, required=True), PositionSkillRequirement(skill_id="branding", minimum_proficiency=70, required=True)],
    pipeline_responsibilities=["creative_pipeline"],
    output_responsibilities=["campaign_strategy"]
)
