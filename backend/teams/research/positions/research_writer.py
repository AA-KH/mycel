from workforce.positions.models import (
    Position, PositionStatus, PositionType, Seniority, Criticality,
    PositionSkillRequirement, PositionToolRequirement, PositionKnowledgeRequirement,
    PositionReasoningRequirement, WorkforceRequirement, Requiredness
)

research_writer = Position(
    position_id="research_writer",
    team_id="research",
    name="Research Writer",
    display_name="Research Writer",
    purpose="Synthesize verified claims and evidence into structured research artifacts, user-facing reports, and downstream-consumable context. Never adds information not in the evidence.",
    status=PositionStatus.ACTIVE,
    position_type=PositionType.SPECIALIST,
    seniority=Seniority.MID,
    criticality=Criticality.HIGH,
    workforce=WorkforceRequirement(
        min_headcount=1, max_headcount=1,
        recommended_headcount=1, requiredness=Requiredness.REQUIRED
    ),
    required_skills=[
        PositionSkillRequirement(skill_id="technical_writing", minimum_proficiency=95, required=True),
        PositionSkillRequirement(skill_id="data_synthesis", minimum_proficiency=90, required=True),
        PositionSkillRequirement(skill_id="report_generation", minimum_proficiency=90, required=True),
        PositionSkillRequirement(skill_id="information_architecture", minimum_proficiency=80, required=True),
        PositionSkillRequirement(skill_id="communication", minimum_proficiency=90, required=True),
        PositionSkillRequirement(skill_id="citation_management", minimum_proficiency=85, required=True),
    ],
    required_tools=[],
    required_knowledge=[
        PositionKnowledgeRequirement(knowledge_space_id="research_methodology", required=True),
        PositionKnowledgeRequirement(knowledge_space_id="technical_writing", required=True),
        PositionKnowledgeRequirement(knowledge_space_id="data_visualization", required=False),
    ],
    reasoning_requirements=[
        PositionReasoningRequirement(preferred_strategy_id="research_verify", required=True),
    ],
    pipeline_responsibilities=["research_pipeline"],
    stage_responsibilities=["synthesize", "review"],
    output_responsibilities=["research_report", "research_artifact", "downstream_context"],
    quality_responsibilities=["report_quality_gate"],
)
