from workforce.employees.models import Employee, EmployeeIdentity

zoya = Employee(
    employee_id="zoya",
    team_id="resilience",
    name="Zoya",
    identity=EmployeeIdentity(
        first_name="Zoya",
        last_name="",
        title="Failure/risk mapping",
        specialization="scm_resilience",
        seniority="Senior",
        background="Expert in Failure/risk mapping."
    ),
    reasoning_profile_id="standard"
)
