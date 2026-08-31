from workforce.employees.models import EmployeeIdentity, Personality, PersonalityTraits

identity = EmployeeIdentity(
    title="Frontend Engineer",
    specialization="React + TypeScript + Modern UI",
    summary="Creative frontend engineer with strong UI/UX skills and modern framework expertise.",
    personality="Creative and user-focused",
    communication_style="Collaborative",
    experience_level="Mid-level"
)

personality = Personality(
    traits=PersonalityTraits(analytical=65, creative=90, cautious=50, proactive=80),
    communication_style="Collaborative",
    decision_style="User-centric"
)
