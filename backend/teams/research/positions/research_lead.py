from workforce.positions.models import (
    Position, PositionStatus, PositionType, Seniority, Criticality,
    PositionSkillRequirement, PositionToolRequirement, PositionKnowledgeRequirement,
    PositionReasoningRequirement, WorkforceRequirement, Requiredness
)

research_lead = Position(
    position_id="research_lead",
    team_id="research",
    name="Research Lead",
    display_name="Research Lead",
    purpose="Guide research strategies and oversee execution of complex analysis tasks.",
    status=PositionStatus.ACTIVE,
    position_type=PositionType.LEADERSHIP,
    seniority=Seniority.LEAD,
    criticality=Criticality.HIGH,
    workforce=WorkforceRequirement(min_headcount=1, max_headcount=5, recommended_headcount=2, requiredness=Requiredness.REQUIRED),
    required_skills=[PositionSkillRequirement(skill_id="research_strategy", minimum_proficiency=70, required=True), PositionSkillRequirement(skill_id="management", minimum_proficiency=70, required=True)],
    pipeline_responsibilities=["research_pipeline"],
    output_responsibilities=["research_strategy"]
)
