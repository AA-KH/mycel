from workforce.employees.models import Employee, EmployeeIdentity

helena = Employee(
    employee_id="helena",
    team_id="council",
    name="Helena",
    identity=EmployeeIdentity(
        first_name="Helena",
        last_name="",
        title="Cost strategist",
        specialization="scm_council",
        seniority="Senior",
        background="Expert in Cost strategist."
    ),
    reasoning_profile_id="standard"
)
