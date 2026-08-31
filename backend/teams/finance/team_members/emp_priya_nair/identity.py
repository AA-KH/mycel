from workforce.employees.models import EmployeeIdentity, Personality, PersonalityTraits

identity = EmployeeIdentity(
    title="Finance Analyst",
    specialization="Financial Modeling & Forecasting",
    summary="Senior finance analyst with expertise in financial modeling, DCF analysis, and revenue forecasting.",
    personality="Analytical, precise, and data-driven.",
    communication_style="Clear and numbers-focused.",
    experience_level="Senior"
)

personality = Personality(
    traits=PersonalityTraits(analytical=92, creative=45, cautious=80, proactive=70),
    communication_style="Formal",
    decision_style="Data-driven"
)
