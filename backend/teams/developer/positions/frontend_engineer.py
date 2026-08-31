from workforce.positions.models import (
    Position, PositionStatus, PositionType, Seniority, Criticality,
    PositionSkillRequirement, PositionToolRequirement, PositionKnowledgeRequirement,
    PositionReasoningRequirement, WorkforceRequirement, Requiredness
)

frontend_engineer = Position(
    position_id="frontend_engineer",
    team_id="developer",
    name="Frontend Engineer",
    display_name="Frontend Engineer",
    purpose="Build and maintain user interfaces, ensuring responsive design and seamless user experience.",
    status=PositionStatus.ACTIVE,
    position_type=PositionType.INDIVIDUAL_CONTRIBUTOR,
    seniority=Seniority.MID,
    criticality=Criticality.HIGH,
    workforce=WorkforceRequirement(
        min_headcount=1, max_headcount=10,
        recommended_headcount=3, requiredness=Requiredness.REQUIRED
    ),
    required_skills=[
        PositionSkillRequirement(skill_id="software_development", minimum_proficiency=75, required=True),
        PositionSkillRequirement(skill_id="frontend_development", minimum_proficiency=80, required=True),
        PositionSkillRequirement(skill_id="ui_ux_design", minimum_proficiency=60, required=True),
        PositionSkillRequirement(skill_id="responsive_design", minimum_proficiency=70, required=True),
        PositionSkillRequirement(skill_id="state_management", minimum_proficiency=65, required=True),
        PositionSkillRequirement(skill_id="software_architecture", minimum_proficiency=55, required=True),
        PositionSkillRequirement(skill_id="testing", minimum_proficiency=50, required=False),
        PositionSkillRequirement(skill_id="version_control", minimum_proficiency=65, required=True),
        PositionSkillRequirement(skill_id="technical_documentation", minimum_proficiency=50, required=False),
    ],
    required_tools=[
        PositionToolRequirement(tool_id="filesystem.read", required=True),
        PositionToolRequirement(tool_id="filesystem.write", required=True),
        PositionToolRequirement(tool_id="browser.devtools", required=True),
        PositionToolRequirement(tool_id="design.tools", required=False),
        PositionToolRequirement(tool_id="git.operations", required=True),
    ],
    required_knowledge=[
        PositionKnowledgeRequirement(knowledge_space_id="software_patterns", required=True),
        PositionKnowledgeRequirement(knowledge_space_id="ui_ux_principles", required=True),
        PositionKnowledgeRequirement(knowledge_space_id="accessibility_standards", required=False),
        PositionKnowledgeRequirement(knowledge_space_id="web_standards", required=True),
    ],
    reasoning_requirements=[
        PositionReasoningRequirement(preferred_strategy_id="code_test", required=False),
    ],
    pipeline_responsibilities=["developer_development"],
    stage_responsibilities=["development", "review"],
    output_responsibilities=["ui_component"],
    quality_responsibilities=["code_review"],
)
