from workforce.employees.models import EmployeeIdentity, Personality, PersonalityTraits

identity = EmployeeIdentity(
    title="Budget Analyst",
    specialization="Budget Planning & Cost Optimization",
    summary="Detail-oriented budget analyst specializing in variance analysis, cost allocation, and financial planning.",
    personality="Methodical, thorough, and cost-conscious.",
    communication_style="Structured and report-oriented.",
    experience_level="Mid-level"
)

personality = Personality(
    traits=PersonalityTraits(analytical=88, creative=40, cautious=85, proactive=65),
    communication_style="Formal",
    decision_style="Conservative"
)
