from workforce.positions.models import (
    Position, PositionStatus, PositionType, Seniority, Criticality,
    PositionSkillRequirement, PositionToolRequirement, PositionKnowledgeRequirement,
    PositionReasoningRequirement, WorkforceRequirement, Requiredness
)

researcher = Position(
    position_id="researcher",
    team_id="research",
    name="Researcher",
    display_name="Researcher",
    purpose="Execute iterative web research to gather evidence, extract claims from sources, track provenance, and identify information gaps. The investigative engine of the research team.",
    status=PositionStatus.ACTIVE,
    position_type=PositionType.SPECIALIST,
    seniority=Seniority.MID,
    criticality=Criticality.HIGH,
    workforce=WorkforceRequirement(
        min_headcount=1, max_headcount=3,
        recommended_headcount=1, requiredness=Requiredness.REQUIRED
    ),
    required_skills=[
        PositionSkillRequirement(skill_id="web_research", minimum_proficiency=95, required=True),
        PositionSkillRequirement(skill_id="information_retrieval", minimum_proficiency=90, required=True),
        PositionSkillRequirement(skill_id="source_analysis", minimum_proficiency=85, required=True),
        PositionSkillRequirement(skill_id="data_extraction", minimum_proficiency=85, required=True),
        PositionSkillRequirement(skill_id="evidence_analysis", minimum_proficiency=80, required=True),
        PositionSkillRequirement(skill_id="competitive_intelligence", minimum_proficiency=80, required=True),
        PositionSkillRequirement(skill_id="query_optimization", minimum_proficiency=80, required=True),
    ],
    required_tools=[
        PositionToolRequirement(tool_id="web.search", required=True),
        PositionToolRequirement(tool_id="browser.open", required=True),
        PositionToolRequirement(tool_id="web.scrape", required=True),
    ],
    required_knowledge=[
        PositionKnowledgeRequirement(knowledge_space_id="web_research", required=True),
        PositionKnowledgeRequirement(knowledge_space_id="source_evaluation", required=True),
        PositionKnowledgeRequirement(knowledge_space_id="data_extraction", required=True),
    ],
    reasoning_requirements=[
        PositionReasoningRequirement(preferred_strategy_id="research_verify", required=True),
    ],
    pipeline_responsibilities=["research_pipeline"],
    stage_responsibilities=["research"],
    output_responsibilities=["evidence_collection", "claim_set"],
    quality_responsibilities=[],
)
