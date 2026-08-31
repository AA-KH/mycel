from workforce.positions.models import (
    Position, PositionStatus, PositionType, Seniority, Criticality,
    PositionSkillRequirement, PositionToolRequirement, PositionKnowledgeRequirement,
    PositionReasoningRequirement, WorkforceRequirement, Requiredness
)

security_engineer = Position(
    position_id="security_engineer",
    team_id="developer",
    name="Security Engineer",
    display_name="Security Engineer",
    purpose="Implement security measures, conduct security audits, and ensure compliance with security standards.",
    status=PositionStatus.ACTIVE,
    position_type=PositionType.SPECIALIST,
    seniority=Seniority.MID,
    criticality=Criticality.HIGH,
    workforce=WorkforceRequirement(
        min_headcount=0, max_headcount=3,
        recommended_headcount=1, requiredness=Requiredness.REQUIRED
    ),
    required_skills=[
        PositionSkillRequirement(skill_id="security_awareness", minimum_proficiency=90, required=True),
        PositionSkillRequirement(skill_id="secure_coding", minimum_proficiency=85, required=True),
        PositionSkillRequirement(skill_id="authentication_authorization", minimum_proficiency=80, required=True),
        PositionSkillRequirement(skill_id="software_development", minimum_proficiency=60, required=True),
        PositionSkillRequirement(skill_id="networking_fundamentals", minimum_proficiency=70, required=True),
        PositionSkillRequirement(skill_id="penetration_testing", minimum_proficiency=65, required=False),
        PositionSkillRequirement(skill_id="compliance", minimum_proficiency=60, required=False),
        PositionSkillRequirement(skill_id="troubleshooting", minimum_proficiency=70, required=True),
        PositionSkillRequirement(skill_id="technical_documentation", minimum_proficiency=70, required=True),
    ],
    required_tools=[
        PositionToolRequirement(tool_id="filesystem.read", required=True),
        PositionToolRequirement(tool_id="security.tools", required=True),
        PositionToolRequirement(tool_id="terminal.execute", required=True),
        PositionToolRequirement(tool_id="git.operations", required=True),
    ],
    required_knowledge=[
        PositionKnowledgeRequirement(knowledge_space_id="security_fundamentals", required=True),
        PositionKnowledgeRequirement(knowledge_space_id="owasp_top_10", required=True),
        PositionKnowledgeRequirement(knowledge_space_id="encryption_standards", required=True),
        PositionKnowledgeRequirement(knowledge_space_id="compliance_standards", required=False),
        PositionKnowledgeRequirement(knowledge_space_id="system_design", required=True),
    ],
    reasoning_requirements=[
        PositionReasoningRequirement(preferred_strategy_id="security_first", required=True),
    ],
    pipeline_responsibilities=["developer_development"],
    stage_responsibilities=["development", "review", "testing"],
    output_responsibilities=["security_audit", "security_policy"],
    quality_responsibilities=["security_review"],
)
