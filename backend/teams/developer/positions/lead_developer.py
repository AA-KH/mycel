from workforce.positions.models import (
    Position, PositionStatus, PositionType, Seniority, Criticality,
    PositionSkillRequirement, PositionToolRequirement, PositionKnowledgeRequirement,
    PositionReasoningRequirement, WorkforceRequirement, Requiredness
)

lead_developer = Position(
    position_id="lead_developer",
    team_id="developer",
    name="Lead Developer",
    display_name="Lead Developer",
    purpose="Lead technical teams, make architectural decisions, mentor developers, and ensure project success.",
    status=PositionStatus.ACTIVE,
    position_type=PositionType.MANAGEMENT,
    seniority=Seniority.SENIOR,
    criticality=Criticality.HIGH,
    workforce=WorkforceRequirement(
        min_headcount=1, max_headcount=3,
        recommended_headcount=1, requiredness=Requiredness.REQUIRED
    ),
    required_skills=[
        PositionSkillRequirement(skill_id="software_development", minimum_proficiency=85, required=True),
        PositionSkillRequirement(skill_id="software_architecture", minimum_proficiency=80, required=True),
        PositionSkillRequirement(skill_id="system_design", minimum_proficiency=75, required=True),
        PositionSkillRequirement(skill_id="backend_development", minimum_proficiency=70, required=True),
        PositionSkillRequirement(skill_id="frontend_development", minimum_proficiency=60, required=False),
        PositionSkillRequirement(skill_id="mentoring", minimum_proficiency=75, required=True),
        PositionSkillRequirement(skill_id="communication", minimum_proficiency=80, required=True),
        PositionSkillRequirement(skill_id="problem_solving", minimum_proficiency=80, required=True),
        PositionSkillRequirement(skill_id="code_review", minimum_proficiency=70, required=True),
        PositionSkillRequirement(skill_id="technical_documentation", minimum_proficiency=70, required=True),
        PositionSkillRequirement(skill_id="agile_methodology", minimum_proficiency=70, required=True),
        PositionSkillRequirement(skill_id="time_management", minimum_proficiency=70, required=True),
    ],
    required_tools=[
        PositionToolRequirement(tool_id="filesystem.read", required=True),
        PositionToolRequirement(tool_id="filesystem.write", required=True),
        PositionToolRequirement(tool_id="terminal.execute", required=True),
        PositionToolRequirement(tool_id="git.operations", required=True),
        PositionToolRequirement(tool_id="project_management", required=True),
    ],
    required_knowledge=[
        PositionKnowledgeRequirement(knowledge_space_id="software_patterns", required=True),
        PositionKnowledgeRequirement(knowledge_space_id="system_design_principles", required=True),
        PositionKnowledgeRequirement(knowledge_space_id="api_standards", required=True),
        PositionKnowledgeRequirement(knowledge_space_id="leadership_principles", required=True),
        PositionKnowledgeRequirement(knowledge_space_id="security_fundamentals", required=True),
    ],
    reasoning_requirements=[
        PositionReasoningRequirement(preferred_strategy_id="plan_validate_execute", required=True),
    ],
    pipeline_responsibilities=["developer_development"],
    stage_responsibilities=["development", "review", "planning"],
    output_responsibilities=["source_code", "architecture_document", "technical_spec"],
    quality_responsibilities=["code_review", "architecture_review"],
)
