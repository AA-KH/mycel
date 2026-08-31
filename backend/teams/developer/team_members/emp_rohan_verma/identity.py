from workforce.employees.models import EmployeeIdentity, Personality, PersonalityTraits

identity = EmployeeIdentity(
    title="QA Engineer",
    specialization="Testing + Automation + Quality Assurance",
    summary="Detail-oriented QA engineer with expertise in automated testing and quality processes.",
    personality="Thorough and quality-focused",
    communication_style="Clear and detailed",
    experience_level="Mid-level"
)

personality = Personality(
    traits=PersonalityTraits(analytical=85, creative=50, cautious=80, proactive=70),
    communication_style="Detailed",
    decision_style="Quality-first"
)
