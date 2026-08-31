from workforce.positions.models import (
    Position, PositionStatus, PositionType, Seniority, Criticality,
    PositionSkillRequirement, PositionToolRequirement, PositionKnowledgeRequirement,
    PositionReasoningRequirement, WorkforceRequirement, Requiredness
)

operations_reviewer = Position(
    position_id="operations_reviewer",
    team_id="operations",
    name="Operations Reviewer",
    display_name="Operations Reviewer",
    purpose="Review operational metrics and approve process changes.",
    status=PositionStatus.ACTIVE,
    position_type=PositionType.REVIEWER,
    seniority=Seniority.SENIOR,
    criticality=Criticality.HIGH,
    workforce=WorkforceRequirement(min_headcount=1, max_headcount=5, recommended_headcount=2, requiredness=Requiredness.REQUIRED),
    required_skills=[PositionSkillRequirement(skill_id="performance_review", minimum_proficiency=70, required=True), PositionSkillRequirement(skill_id="quality_assurance", minimum_proficiency=70, required=True)],
    pipeline_responsibilities=["operations_review_pipeline"],
    output_responsibilities=["performance_review"]
)
