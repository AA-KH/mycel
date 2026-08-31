from workforce.positions.models import (
    Position, PositionStatus, PositionType, Seniority, Criticality,
    PositionSkillRequirement, PositionToolRequirement, PositionKnowledgeRequirement,
    PositionReasoningRequirement, WorkforceRequirement, Requiredness
)

financial_planner = Position(
    position_id="financial_planner",
    team_id="finance",
    name="Financial Planner",
    display_name="Financial Planner",
    purpose="Develop financial plans, budgets, and forecasts for the organization.",
    status=PositionStatus.ACTIVE,
    position_type=PositionType.SPECIALIST,
    seniority=Seniority.SENIOR,
    criticality=Criticality.HIGH,
    workforce=WorkforceRequirement(min_headcount=1, max_headcount=5, recommended_headcount=2, requiredness=Requiredness.REQUIRED),
    required_skills=[PositionSkillRequirement(skill_id="budgeting", minimum_proficiency=70, required=True), PositionSkillRequirement(skill_id="forecasting", minimum_proficiency=70, required=True)],
    pipeline_responsibilities=["planning_pipeline"],
    output_responsibilities=["budget_plan"]
)
