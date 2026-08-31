from workforce.employees.models import Employee, EmployeeIdentity

omar = Employee(
    employee_id="omar",
    team_id="council",
    name="Omar",
    identity=EmployeeIdentity(
        first_name="Omar",
        last_name="",
        title="Risk/compliance strategist",
        specialization="scm_council",
        seniority="Senior",
        background="Expert in Risk/compliance strategist."
    ),
    reasoning_profile_id="standard"
)
