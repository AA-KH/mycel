from workforce.employees.models import EmployeeIdentity, Personality, PersonalityTraits

identity = EmployeeIdentity(
    title="DevOps Engineer",
    specialization="Docker + Kubernetes + CI/CD + Cloud",
    summary="Skilled DevOps engineer with expertise in containerization, automation, and cloud infrastructure.",
    personality="Process-oriented and reliable",
    communication_style="Clear and structured",
    experience_level="Mid-level"
)

personality = Personality(
    traits=PersonalityTraits(analytical=80, creative=55, cautious=75, proactive=85),
    communication_style="Structured",
    decision_style="Process-driven"
)
