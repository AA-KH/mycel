from workforce.employees.models import EmployeeIdentity, Personality, PersonalityTraits

identity = EmployeeIdentity(
    title="Full Stack Engineer",
    specialization="React + Node.js + MongoDB",
    summary="Versatile full-stack engineer capable of handling both frontend and backend development.",
    personality="Adaptable and comprehensive",
    communication_style="Clear and versatile",
    experience_level="Mid-level"
)

personality = Personality(
    traits=PersonalityTraits(analytical=75, creative=70, cautious=60, proactive=80),
    communication_style="Versatile",
    decision_style="Balanced"
)
