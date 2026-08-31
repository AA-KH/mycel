from workforce.employees.models import Employee, EmployeeIdentity

sofia = Employee(
    employee_id="sofia",
    team_id="council",
    name="Sofia",
    identity=EmployeeIdentity(
        first_name="Sofia",
        last_name="",
        title="Council chair",
        specialization="scm_council",
        seniority="Senior",
        background="Expert in Council chair."
    ),
    reasoning_profile_id="standard"
)
