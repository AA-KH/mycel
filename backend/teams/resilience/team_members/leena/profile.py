from workforce.employees.models import Employee, EmployeeIdentity

leena = Employee(
    employee_id="leena",
    team_id="resilience",
    name="Leena",
    identity=EmployeeIdentity(
        first_name="Leena",
        last_name="",
        title="Stress testing",
        specialization="scm_resilience",
        seniority="Senior",
        background="Expert in Stress testing."
    ),
    reasoning_profile_id="standard"
)
