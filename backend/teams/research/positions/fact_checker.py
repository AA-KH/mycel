from workforce.positions.models import (
    Position, PositionStatus, PositionType, Seniority, Criticality,
    PositionSkillRequirement, PositionToolRequirement, PositionKnowledgeRequirement,
    PositionReasoningRequirement, WorkforceRequirement, Requiredness
)

fact_checker = Position(
    position_id="fact_checker",
    team_id="research",
    name="Fact Checker",
    display_name="Fact Checker",
    purpose="Independently verify claims through separate search, detect source conflicts, assess evidence quality, and never manufacture certainty. The Zero-Hallucination enforcer.",
    status=PositionStatus.ACTIVE,
    position_type=PositionType.REVIEWER,
    seniority=Seniority.SENIOR,
    criticality=Criticality.CRITICAL,
    workforce=WorkforceRequirement(
        min_headcount=1, max_headcount=1,
        recommended_headcount=1, requiredness=Requiredness.REQUIRED
    ),
    required_skills=[
        PositionSkillRequirement(skill_id="fact_verification", minimum_proficiency=95, required=True),
        PositionSkillRequirement(skill_id="source_validation", minimum_proficiency=95, required=True),
        PositionSkillRequirement(skill_id="critical_thinking", minimum_proficiency=95, required=True),
        PositionSkillRequirement(skill_id="evidence_analysis", minimum_proficiency=90, required=True),
        PositionSkillRequirement(skill_id="conflict_detection", minimum_proficiency=90, required=True),
        PositionSkillRequirement(skill_id="web_research", minimum_proficiency=80, required=True),
    ],
    required_tools=[
        PositionToolRequirement(tool_id="web.search", required=True),
        PositionToolRequirement(tool_id="browser.open", required=True),
    ],
    required_knowledge=[
        PositionKnowledgeRequirement(knowledge_space_id="fact_checking_methodology", required=True),
        PositionKnowledgeRequirement(knowledge_space_id="source_evaluation", required=True),
        PositionKnowledgeRequirement(knowledge_space_id="media_literacy", required=True),
    ],
    reasoning_requirements=[
        PositionReasoningRequirement(preferred_strategy_id="research_verify", required=True),
    ],
    pipeline_responsibilities=["research_pipeline"],
    stage_responsibilities=["verify"],
    output_responsibilities=["verification_report"],
    quality_responsibilities=["evidence_quality_gate", "research_quality_gate"],
)
