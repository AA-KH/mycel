from workforce.positions.models import (
    Position, PositionStatus, PositionType, Seniority, Criticality,
    PositionSkillRequirement, PositionToolRequirement, PositionKnowledgeRequirement,
    PositionReasoningRequirement, WorkforceRequirement, Requiredness
)

graphic_designer = Position(
    position_id="graphic_designer",
    team_id="creative",
    name="Graphic Designer",
    display_name="Graphic Designer",
    purpose=(
        "Design visual assets, illustrations, marketing imagery, and brand materials. "
        "A Graphic Designer owns the full visual production lifecycle: from brief intake "
        "and concept development through storyboarding, AI-assisted asset generation, "
        "iterative design review, and final artifact delivery."
    ),
    status=PositionStatus.ACTIVE,
    position_type=PositionType.SPECIALIST,
    seniority=Seniority.MID,
    criticality=Criticality.HIGH,
    workforce=WorkforceRequirement(
        min_headcount=1,
        max_headcount=5,
        recommended_headcount=2,
        requiredness=Requiredness.REQUIRED
    ),
    required_skills=[
        # Core visual craft
        PositionSkillRequirement(skill_id="visual_design",    minimum_proficiency=70, required=True),
        PositionSkillRequirement(skill_id="composition",      minimum_proficiency=65, required=True),
        PositionSkillRequirement(skill_id="typography",       minimum_proficiency=65, required=True),
        PositionSkillRequirement(skill_id="color_theory",     minimum_proficiency=65, required=True),
        # Brand & identity
        PositionSkillRequirement(skill_id="branding",         minimum_proficiency=60, required=True),
        # Quality gate
        PositionSkillRequirement(skill_id="design_review",    minimum_proficiency=60, required=True),
        # Preferred (not required but expected at senior level)
        PositionSkillRequirement(skill_id="storyboarding",    minimum_proficiency=50, required=False),
        PositionSkillRequirement(skill_id="ai_image_generation", minimum_proficiency=50, required=False),
        PositionSkillRequirement(skill_id="illustration",     minimum_proficiency=55, required=False),
    ],
    pipeline_responsibilities=["creative_pipeline", "design_asset_creation"],
    output_responsibilities=["marketing_image", "design_asset", "social_media_asset", "brand_asset"]
)

