from workforce.positions.models import (
    Position, PositionStatus, PositionType, Seniority, Criticality,
    PositionSkillRequirement, PositionToolRequirement, PositionKnowledgeRequirement,
    PositionReasoningRequirement, WorkforceRequirement, Requiredness
)

devops_engineer = Position(
    position_id="devops_engineer",
    team_id="developer",
    name="DevOps Engineer",
    display_name="DevOps Engineer",
    purpose="Automate infrastructure, manage CI/CD pipelines, and ensure reliable deployments.",
    status=PositionStatus.ACTIVE,
    position_type=PositionType.SPECIALIST,
    seniority=Seniority.MID,
    criticality=Criticality.HIGH,
    workforce=WorkforceRequirement(
        min_headcount=1, max_headcount=5,
        recommended_headcount=2, requiredness=Requiredness.REQUIRED
    ),
    required_skills=[
        PositionSkillRequirement(skill_id="software_development", minimum_proficiency=60, required=True),
        PositionSkillRequirement(skill_id="devops", minimum_proficiency=80, required=True),
        PositionSkillRequirement(skill_id="version_control", minimum_proficiency=85, required=True),
        PositionSkillRequirement(skill_id="ci_cd", minimum_proficiency=75, required=True),
        PositionSkillRequirement(skill_id="containerization", minimum_proficiency=70, required=True),
        PositionSkillRequirement(skill_id="cloud_services", minimum_proficiency=65, required=True),
        PositionSkillRequirement(skill_id="infrastructure_as_code", minimum_proficiency=65, required=True),
        PositionSkillRequirement(skill_id="monitoring", minimum_proficiency=60, required=True),
        PositionSkillRequirement(skill_id="security_awareness", minimum_proficiency=55, required=True),
        PositionSkillRequirement(skill_id="troubleshooting", minimum_proficiency=70, required=True),
    ],
    required_tools=[
        PositionToolRequirement(tool_id="filesystem.read", required=True),
        PositionToolRequirement(tool_id="filesystem.write", required=True),
        PositionToolRequirement(tool_id="terminal.execute", required=True),
        PositionToolRequirement(tool_id="docker.operations", required=True),
        PositionToolRequirement(tool_id="kubernetes.operations", required=True),
        PositionToolRequirement(tool_id="cloud.cli", required=True),
        PositionToolRequirement(tool_id="git.operations", required=True),
    ],
    required_knowledge=[
        PositionKnowledgeRequirement(knowledge_space_id="system_design", required=True),
        PositionKnowledgeRequirement(knowledge_space_id="security_fundamentals", required=True),
        PositionKnowledgeRequirement(knowledge_space_id="cloud_architecture", required=True),
        PositionKnowledgeRequirement(knowledge_space_id="networking_fundamentals", required=True),
        PositionKnowledgeRequirement(knowledge_space_id="deployment_strategies", required=True),
    ],
    reasoning_requirements=[
        PositionReasoningRequirement(preferred_strategy_id="code_test", required=False),
    ],
    pipeline_responsibilities=["developer_development"],
    stage_responsibilities=["review"],
    output_responsibilities=["deployment_config"],
    quality_responsibilities=["code_review"],
)
