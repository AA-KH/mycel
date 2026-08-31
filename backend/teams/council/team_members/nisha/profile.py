from workforce.employees.models import Employee, EmployeeIdentity

nisha = Employee(
    employee_id="nisha",
    team_id="council",
    name="Nisha",
    identity=EmployeeIdentity(
        first_name="Nisha",
        last_name="",
        title="Operations strategist",
        specialization="scm_council",
        seniority="Senior",
        background="Expert in Operations strategist."
    ),
    reasoning_profile_id="standard"
)
