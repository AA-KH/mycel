from workforce.positions.models import (
    Position, PositionStatus, PositionType, Seniority, Criticality,
    PositionSkillRequirement, PositionToolRequirement, PositionKnowledgeRequirement,
    PositionReasoningRequirement, WorkforceRequirement, Requiredness
)

operations_coordinator = Position(
    position_id="operations_coordinator",
    team_id="operations",
    name="Operations Coordinator",
    display_name="Operations Coordinator",
    purpose="Coordinate resources, schedules, and cross-functional operational tasks.",
    status=PositionStatus.ACTIVE,
    position_type=PositionType.INDIVIDUAL_CONTRIBUTOR,
    seniority=Seniority.MID,
    criticality=Criticality.HIGH,
    workforce=WorkforceRequirement(min_headcount=1, max_headcount=5, recommended_headcount=2, requiredness=Requiredness.REQUIRED),
    required_skills=[PositionSkillRequirement(skill_id="project_coordination", minimum_proficiency=70, required=True), PositionSkillRequirement(skill_id="logistics", minimum_proficiency=70, required=True)],
    pipeline_responsibilities=["coordination_pipeline"],
    output_responsibilities=["schedule"]
)
