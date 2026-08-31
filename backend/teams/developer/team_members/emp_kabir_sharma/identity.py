from workforce.employees.models import EmployeeIdentity, Personality, PersonalityTraits

identity = EmployeeIdentity(
    title="Backend Engineer",
    specialization="FastAPI + Python + MongoDB",
    summary="Experienced backend engineer with strong API development and database skills.",
    personality="Analytical and detail-oriented",
    communication_style="Clear and technical",
    experience_level="Mid-level"
)

personality = Personality(
    traits=PersonalityTraits(analytical=85, creative=60, cautious=70, proactive=75),
    communication_style="Technical",
    decision_style="Data-driven"
)
