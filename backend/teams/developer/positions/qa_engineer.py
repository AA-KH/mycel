from workforce.positions.models import (
    Position, PositionStatus, PositionType, Seniority, Criticality,
    PositionSkillRequirement, PositionToolRequirement, PositionKnowledgeRequirement,
    PositionReasoningRequirement, WorkforceRequirement, Requiredness
)

qa_engineer = Position(
    position_id="qa_engineer",
    team_id="developer",
    name="QA Engineer",
    display_name="QA Engineer",
    purpose="Design and execute test strategies to ensure software quality and reliability.",
    status=PositionStatus.ACTIVE,
    position_type=PositionType.SPECIALIST,
    seniority=Seniority.MID,
    criticality=Criticality.HIGH,
    workforce=WorkforceRequirement(
        min_headcount=1, max_headcount=5,
        recommended_headcount=2, requiredness=Requiredness.REQUIRED
    ),
    required_skills=[
        PositionSkillRequirement(skill_id="testing", minimum_proficiency=85, required=True),
        PositionSkillRequirement(skill_id="unit_testing", minimum_proficiency=75, required=True),
        PositionSkillRequirement(skill_id="integration_testing", minimum_proficiency=75, required=True),
        PositionSkillRequirement(skill_id="e2e_testing", minimum_proficiency=70, required=True),
        PositionSkillRequirement(skill_id="test_automation", minimum_proficiency=80, required=True),
        PositionSkillRequirement(skill_id="code_review", minimum_proficiency=70, required=True),
        PositionSkillRequirement(skill_id="quality_assurance", minimum_proficiency=75, required=True),
        PositionSkillRequirement(skill_id="debugging", minimum_proficiency=65, required=True),
        PositionSkillRequirement(skill_id="technical_documentation", minimum_proficiency=60, required=True),
        PositionSkillRequirement(skill_id="troubleshooting", minimum_proficiency=70, required=True),
    ],
    required_tools=[
        PositionToolRequirement(tool_id="filesystem.read", required=True),
        PositionToolRequirement(tool_id="filesystem.write", required=True),
        PositionToolRequirement(tool_id="test.frameworks", required=True),
        PositionToolRequirement(tool_id="automation.tools", required=True),
        PositionToolRequirement(tool_id="git.operations", required=True),
    ],
    required_knowledge=[
        PositionKnowledgeRequirement(knowledge_space_id="testing_methodology", required=True),
        PositionKnowledgeRequirement(knowledge_space_id="quality_standards", required=True),
        PositionKnowledgeRequirement(knowledge_space_id="automation_frameworks", required=True),
        PositionKnowledgeRequirement(knowledge_space_id="software_patterns", required=False),
    ],
    reasoning_requirements=[
        PositionReasoningRequirement(preferred_strategy_id="code_test", required=False),
    ],
    pipeline_responsibilities=["developer_development"],
    stage_responsibilities=["testing", "review"],
    output_responsibilities=["test_suite"],
    quality_responsibilities=["code_review"],
)
