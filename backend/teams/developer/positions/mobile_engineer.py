from workforce.positions.models import (
    Position, PositionStatus, PositionType, Seniority, Criticality,
    PositionSkillRequirement, PositionToolRequirement, PositionKnowledgeRequirement,
    PositionReasoningRequirement, WorkforceRequirement, Requiredness
)

mobile_engineer = Position(
    position_id="mobile_engineer",
    team_id="developer",
    name="Mobile Engineer",
    display_name="Mobile Engineer",
    purpose="Develop native and cross-platform mobile applications for iOS and Android.",
    status=PositionStatus.ACTIVE,
    position_type=PositionType.INDIVIDUAL_CONTRIBUTOR,
    seniority=Seniority.MID,
    criticality=Criticality.MEDIUM,
    workforce=WorkforceRequirement(
        min_headcount=0, max_headcount=5,
        recommended_headcount=2, requiredness=Requiredness.OPTIONAL
    ),
    required_skills=[
        PositionSkillRequirement(skill_id="software_development", minimum_proficiency=70, required=True),
        PositionSkillRequirement(skill_id="mobile_development", minimum_proficiency=75, required=True),
        PositionSkillRequirement(skill_id="react_native", minimum_proficiency=60, required=False),
        PositionSkillRequirement(skill_id="flutter", minimum_proficiency=60, required=False),
        PositionSkillRequirement(skill_id="debugging", minimum_proficiency=65, required=True),
        PositionSkillRequirement(skill_id="testing", minimum_proficiency=55, required=False),
        PositionSkillRequirement(skill_id="version_control", minimum_proficiency=65, required=True),
        PositionSkillRequirement(skill_id="api_integration", minimum_proficiency=60, required=True),
        PositionSkillRequirement(skill_id="technical_documentation", minimum_proficiency=50, required=False),
    ],
    required_tools=[
        PositionToolRequirement(tool_id="filesystem.read", required=True),
        PositionToolRequirement(tool_id="filesystem.write", required=True),
        PositionToolRequirement(tool_id="mobile.simulators", required=True),
        PositionToolRequirement(tool_id="git.operations", required=True),
    ],
    required_knowledge=[
        PositionKnowledgeRequirement(knowledge_space_id="mobile_patterns", required=True),
        PositionKnowledgeRequirement(knowledge_space_id="mobile_ui_guidelines", required=True),
        PositionKnowledgeRequirement(knowledge_space_id="api_standards", required=True),
        PositionKnowledgeRequirement(knowledge_space_id="software_patterns", required=False),
    ],
    reasoning_requirements=[
        PositionReasoningRequirement(preferred_strategy_id="code_test", required=False),
    ],
    pipeline_responsibilities=["developer_development"],
    stage_responsibilities=["development", "testing"],
    output_responsibilities=["mobile_app", "ui_component"],
    quality_responsibilities=["code_review"],
)
