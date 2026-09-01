from workforce.employees.models import Employee, EmployeeIdentity

arjun = Employee(
    employee_id="arjun",
    team_id="resilience",
    name="Arjun",
    identity=EmployeeIdentity(
        first_name="Arjun",
        last_name="",
        title="Business Continuity & Recovery Planner",
        specialization="scm_resilience",
        seniority="Senior",
        background="Expert in Business Continuity Planning, Financial Risk Mitigation, and developing actionable supply chain recovery strategies."
    ),
    reasoning_profile_id="standard"
)
