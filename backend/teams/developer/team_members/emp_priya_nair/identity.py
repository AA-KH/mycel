from workforce.employees.models import EmployeeIdentity, Personality, PersonalityTraits

identity = EmployeeIdentity(
    title="Lead Developer",
    specialization="Technical Leadership + Architecture",
    summary="Experienced technical leader with strong architectural skills and team mentoring abilities.",
    personality="Strategic and supportive",
    communication_style="Clear and inspiring",
    experience_level="Senior"
)

personality = Personality(
    traits=PersonalityTraits(analytical=90, creative=70, cautious=65, proactive=85),
    communication_style="Inspiring",
    decision_style="Strategic"
)
