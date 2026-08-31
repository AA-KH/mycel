from workforce.positions.models import (
    Position, PositionStatus, PositionType, Seniority, Criticality,
    PositionSkillRequirement, PositionToolRequirement, PositionKnowledgeRequirement,
    PositionReasoningRequirement, WorkforceRequirement, Requiredness
)

research_analyst = Position(
    position_id="research_analyst",
    team_id="research",
    name="Research Analyst",
    display_name="Research Analyst",
    purpose="Analyze research requests, decompose into structured research plans, identify information requirements, and define acceptance criteria for evidence sufficiency.",
    status=PositionStatus.ACTIVE,
    position_type=PositionType.LEADERSHIP,
    seniority=Seniority.SENIOR,
    criticality=Criticality.HIGH,
    workforce=WorkforceRequirement(
        min_headcount=1, max_headcount=1,
        recommended_headcount=1, requiredness=Requiredness.REQUIRED
    ),
    required_skills=[
        PositionSkillRequirement(skill_id="research_methodology", minimum_proficiency=90, required=True),
        PositionSkillRequirement(skill_id="analytical_thinking", minimum_proficiency=90, required=True),
        PositionSkillRequirement(skill_id="information_architecture", minimum_proficiency=80, required=True),
        PositionSkillRequirement(skill_id="strategic_planning", minimum_proficiency=85, required=True),
        PositionSkillRequirement(skill_id="communication", minimum_proficiency=85, required=True),
        PositionSkillRequirement(skill_id="problem_decomposition", minimum_proficiency=90, required=True),
        PositionSkillRequirement(skill_id="source_evaluation", minimum_proficiency=85, required=True),
    ],
    required_tools=[
        PositionToolRequirement(tool_id="web.search", required=True),
    ],
    required_knowledge=[
        PositionKnowledgeRequirement(knowledge_space_id="research_methodology", required=True),
        PositionKnowledgeRequirement(knowledge_space_id="information_architecture", required=True),
        PositionKnowledgeRequirement(knowledge_space_id="source_evaluation", required=True),
    ],
    reasoning_requirements=[
        PositionReasoningRequirement(preferred_strategy_id="research_verify", required=True),
    ],
    pipeline_responsibilities=["research_pipeline"],
    stage_responsibilities=["analyze", "review"],
    output_responsibilities=["research_plan", "research_report"],
    quality_responsibilities=["research_quality_gate"],
)
