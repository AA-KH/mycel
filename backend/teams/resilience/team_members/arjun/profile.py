from workforce.employees.models import Employee, EmployeeIdentity

arjun = Employee(
    employee_id="arjun",
    team_id="resilience",
    name="Arjun",
    identity=EmployeeIdentity(
        first_name="Arjun",
        last_name="",
        title="Continuity & recovery planning",
        specialization="scm_resilience",
        seniority="Senior",
        background="Expert in Continuity & recovery planning."
    ),
    reasoning_profile_id="standard"
)
