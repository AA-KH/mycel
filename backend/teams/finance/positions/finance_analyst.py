from workforce.positions.models import (
    Position, PositionStatus, PositionType, Seniority, Criticality,
    PositionSkillRequirement, PositionToolRequirement, PositionKnowledgeRequirement,
    PositionReasoningRequirement, WorkforceRequirement, Requiredness
)

finance_analyst = Position(
    position_id="finance_analyst",
    team_id="finance",
    name="Finance Analyst",
    display_name="Finance Analyst",
    purpose="Analyze financial data, prepare financial models, generate forecasts, and provide actionable insights for decision-making.",
    status=PositionStatus.ACTIVE,
    position_type=PositionType.SPECIALIST,
    seniority=Seniority.MID,
    criticality=Criticality.HIGH,
    workforce=WorkforceRequirement(
        min_headcount=1, max_headcount=5,
        recommended_headcount=2, requiredness=Requiredness.REQUIRED
    ),
    required_skills=[
        PositionSkillRequirement(skill_id="financial_modeling", minimum_proficiency=80, required=True),
        PositionSkillRequirement(skill_id="data_analysis", minimum_proficiency=75, required=True),
        PositionSkillRequirement(skill_id="financial_reporting", minimum_proficiency=70, required=True),
        PositionSkillRequirement(skill_id="forecasting", minimum_proficiency=70, required=True),
        PositionSkillRequirement(skill_id="risk_assessment", minimum_proficiency=65, required=True),
        PositionSkillRequirement(skill_id="accounting", minimum_proficiency=60, required=False),
        PositionSkillRequirement(skill_id="cost_analysis", minimum_proficiency=65, required=False),
    ],
    required_tools=[
        PositionToolRequirement(tool_id="spreadsheet.processing", required=True),
        PositionToolRequirement(tool_id="financial.calculator", required=True),
        PositionToolRequirement(tool_id="data.analysis", required=True),
        PositionToolRequirement(tool_id="reporting.tools", required=True),
        PositionToolRequirement(tool_id="document.generation", required=True),
        PositionToolRequirement(tool_id="database.query", required=False),
    ],
    required_knowledge=[
        PositionKnowledgeRequirement(knowledge_space_id="financial_analysis", required=True),
        PositionKnowledgeRequirement(knowledge_space_id="financial_markets", required=True),
        PositionKnowledgeRequirement(knowledge_space_id="accounting_fundamentals", required=True),
        PositionKnowledgeRequirement(knowledge_space_id="financial_reporting_standards", required=False),
        PositionKnowledgeRequirement(knowledge_space_id="cost_management", required=False),
    ],
    reasoning_requirements=[
        PositionReasoningRequirement(preferred_strategy_id="financial_analysis_reasoning", required=True),
    ],
    pipeline_responsibilities=["finance_pipeline"],
    stage_responsibilities=["analysis", "modeling", "forecasting"],
    output_responsibilities=["financial_report", "financial_model", "forecast"],
    quality_responsibilities=["accuracy_validation", "model_review"],
)
