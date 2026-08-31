from workforce.positions.models import (
    Position, PositionStatus, PositionType, Seniority, Criticality,
    PositionSkillRequirement, PositionToolRequirement, PositionKnowledgeRequirement,
    PositionReasoningRequirement, WorkforceRequirement, Requiredness
)

finance_reviewer = Position(
    position_id="finance_reviewer",
    team_id="finance",
    name="Finance Reviewer",
    display_name="Finance Reviewer",
    purpose="Review and approve financial models, budgets, and compliance reports.",
    status=PositionStatus.ACTIVE,
    position_type=PositionType.REVIEWER,
    seniority=Seniority.SENIOR,
    criticality=Criticality.HIGH,
    workforce=WorkforceRequirement(min_headcount=1, max_headcount=5, recommended_headcount=2, requiredness=Requiredness.REQUIRED),
    required_skills=[PositionSkillRequirement(skill_id="financial_review", minimum_proficiency=70, required=True), PositionSkillRequirement(skill_id="compliance", minimum_proficiency=70, required=True)],
    pipeline_responsibilities=["finance_approval_pipeline"],
    output_responsibilities=["approved_budget"]
)
