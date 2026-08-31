from workforce.positions.models import (
    Position, PositionStatus, PositionType, Seniority, Criticality,
    PositionSkillRequirement, PositionToolRequirement, PositionKnowledgeRequirement,
    PositionReasoningRequirement, WorkforceRequirement, Requiredness
)

backend_engineer = Position(
    position_id="backend_engineer",
    team_id="developer",
    name="Backend Engineer",
    display_name="Backend Engineer",
    purpose="Design, implement, and maintain server-side applications, APIs, and data pipelines.",
    status=PositionStatus.ACTIVE,
    position_type=PositionType.INDIVIDUAL_CONTRIBUTOR,
    seniority=Seniority.MID,
    criticality=Criticality.HIGH,
    workforce=WorkforceRequirement(
        min_headcount=1, max_headcount=10,
        recommended_headcount=3, requiredness=Requiredness.REQUIRED
    ),
    required_skills=[
        PositionSkillRequirement(skill_id="software_development", minimum_proficiency=80, required=True),
        PositionSkillRequirement(skill_id="backend_development", minimum_proficiency=75, required=True),
        PositionSkillRequirement(skill_id="debugging", minimum_proficiency=70, required=True),
        PositionSkillRequirement(skill_id="software_architecture", minimum_proficiency=60, required=True),
        PositionSkillRequirement(skill_id="api_development", minimum_proficiency=70, required=True),
        PositionSkillRequirement(skill_id="database_management", minimum_proficiency=65, required=True),
        PositionSkillRequirement(skill_id="testing", minimum_proficiency=60, required=False),
        PositionSkillRequirement(skill_id="security_awareness", minimum_proficiency=50, required=False),
        PositionSkillRequirement(skill_id="version_control", minimum_proficiency=70, required=True),
        PositionSkillRequirement(skill_id="technical_documentation", minimum_proficiency=50, required=False),
    ],
    required_tools=[
        PositionToolRequirement(tool_id="filesystem.read", required=True),
        PositionToolRequirement(tool_id="filesystem.write", required=True),
        PositionToolRequirement(tool_id="terminal.execute", required=True),
        PositionToolRequirement(tool_id="database.query", required=True),
        PositionToolRequirement(tool_id="git.operations", required=True),
    ],
    required_knowledge=[
        PositionKnowledgeRequirement(knowledge_space_id="software_patterns", required=True),
        PositionKnowledgeRequirement(knowledge_space_id="api_standards", required=True),
        PositionKnowledgeRequirement(knowledge_space_id="database_design", required=True),
        PositionKnowledgeRequirement(knowledge_space_id="security_fundamentals", required=False),
        PositionKnowledgeRequirement(knowledge_space_id="system_design_principles", required=True),
    ],
    reasoning_requirements=[
        PositionReasoningRequirement(preferred_strategy_id="code_test", required=False),
    ],
    pipeline_responsibilities=["developer_development"],
    stage_responsibilities=["development", "testing"],
    output_responsibilities=["source_code"],
    quality_responsibilities=["code_review"],
)
