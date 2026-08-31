from workforce.positions.models import (
    Position, PositionStatus, PositionType, Seniority, Criticality,
    PositionSkillRequirement, PositionToolRequirement, PositionKnowledgeRequirement,
    PositionReasoningRequirement, WorkforceRequirement, Requiredness
)

budget_analyst = Position(
    position_id="budget_analyst",
    team_id="finance",
    name="Budget Analyst",
    display_name="Budget Analyst",
    purpose="Create, manage, and monitor organizational budgets, analyze spending patterns, and recommend cost optimization strategies.",
    status=PositionStatus.ACTIVE,
    position_type=PositionType.SPECIALIST,
    seniority=Seniority.MID,
    criticality=Criticality.HIGH,
    workforce=WorkforceRequirement(
        min_headcount=1, max_headcount=5,
        recommended_headcount=2, requiredness=Requiredness.REQUIRED
    ),
    required_skills=[
        PositionSkillRequirement(skill_id="budgeting", minimum_proficiency=80, required=True),
        PositionSkillRequirement(skill_id="cost_analysis", minimum_proficiency=75, required=True),
        PositionSkillRequirement(skill_id="forecasting", minimum_proficiency=70, required=True),
        PositionSkillRequirement(skill_id="data_analysis", minimum_proficiency=70, required=True),
        PositionSkillRequirement(skill_id="financial_modeling", minimum_proficiency=65, required=True),
        PositionSkillRequirement(skill_id="financial_reporting", minimum_proficiency=60, required=False),
        PositionSkillRequirement(skill_id="risk_assessment", minimum_proficiency=55, required=False),
    ],
    required_tools=[
        PositionToolRequirement(tool_id="spreadsheet.processing", required=True),
        PositionToolRequirement(tool_id="financial.calculator", required=True),
        PositionToolRequirement(tool_id="data.analysis", required=True),
        PositionToolRequirement(tool_id="reporting.tools", required=True),
        PositionToolRequirement(tool_id="document.generation", required=True),
    ],
    required_knowledge=[
        PositionKnowledgeRequirement(knowledge_space_id="budgeting_principles", required=True),
        PositionKnowledgeRequirement(knowledge_space_id="cost_management", required=True),
        PositionKnowledgeRequirement(knowledge_space_id="financial_analysis", required=True),
        PositionKnowledgeRequirement(knowledge_space_id="accounting_fundamentals", required=False),
    ],
    reasoning_requirements=[
        PositionReasoningRequirement(preferred_strategy_id="budget_optimization", required=True),
    ],
    pipeline_responsibilities=["budget_pipeline"],
    stage_responsibilities=["planning", "allocation", "monitoring"],
    output_responsibilities=["budget_plan", "variance_report", "cost_optimization_recommendation"],
    quality_responsibilities=["budget_accuracy", "variance_analysis"],
)
