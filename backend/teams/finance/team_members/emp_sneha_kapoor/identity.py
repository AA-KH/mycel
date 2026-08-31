from workforce.employees.models import EmployeeIdentity, Personality, PersonalityTraits

identity = EmployeeIdentity(
    title="Accounts Specialist",
    specialization="Accounting & Reconciliation",
    summary="Experienced accounts specialist with deep expertise in bookkeeping, reconciliation, and regulatory compliance.",
    personality="Meticulous, rule-oriented, and dependable.",
    communication_style="Precise and documentation-focused.",
    experience_level="Senior"
)

personality = Personality(
    traits=PersonalityTraits(analytical=85, creative=35, cautious=90, proactive=60),
    communication_style="Formal",
    decision_style="Rule-based"
)
