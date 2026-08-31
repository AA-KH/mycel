from workforce.positions.models import (
    Position, PositionStatus, PositionType, Seniority, Criticality,
    PositionSkillRequirement, PositionToolRequirement, PositionKnowledgeRequirement,
    PositionReasoningRequirement, WorkforceRequirement, Requiredness
)

video_producer = Position(
    position_id="video_producer",
    team_id="creative",
    name="Video Producer",
    display_name="Video Producer",
    purpose="Oversee and manage the end-to-end production of promotional videos.",
    status=PositionStatus.ACTIVE,
    position_type=PositionType.INDIVIDUAL_CONTRIBUTOR,
    seniority=Seniority.MID,
    criticality=Criticality.HIGH,
    workforce=WorkforceRequirement(min_headcount=1, max_headcount=5, recommended_headcount=2, requiredness=Requiredness.REQUIRED),
    required_skills=[PositionSkillRequirement(skill_id="video_production", minimum_proficiency=70, required=True), PositionSkillRequirement(skill_id="storytelling", minimum_proficiency=70, required=True)],
    pipeline_responsibilities=["promotional_video_pipeline"],
    output_responsibilities=["promotional_video"]
)
