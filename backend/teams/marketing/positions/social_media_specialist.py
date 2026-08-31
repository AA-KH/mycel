# Position definitions for social_media_specialist
# Note: Social media responsibilities are handled by the content_creator (Karan)
# and growth_specialist (Simran) positions.
# This stub is retained for backward compatibility.

from workforce.positions.models import (
    Position, PositionStatus, PositionType, Seniority, Criticality,
    PositionSkillRequirement, PositionToolRequirement, PositionKnowledgeRequirement,
    PositionReasoningRequirement, WorkforceRequirement, Requiredness
)

social_media_specialist = Position(
    position_id="social_media_specialist",
    team_id="marketing",
    name="Social Media Specialist",
    display_name="Social Media Specialist",
    purpose="Manage social media presence across platforms. (Covered by Content Creator and Growth Specialist roles.)",
    status=PositionStatus.INACTIVE,
    position_type=PositionType.INDIVIDUAL_CONTRIBUTOR,
    seniority=Seniority.MID,
    criticality=Criticality.MEDIUM,
    workforce=WorkforceRequirement(min_headcount=0, max_headcount=1, recommended_headcount=0, requiredness=Requiredness.OPTIONAL),
    required_skills=[PositionSkillRequirement(skill_id="social_media_marketing", minimum_proficiency=70, required=True)],
    pipeline_responsibilities=["marketing_pipeline"],
    output_responsibilities=["social_post"]
)
