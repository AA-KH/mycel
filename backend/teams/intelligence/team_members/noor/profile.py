from workforce.employees.models import Employee, EmployeeIdentity

noor = Employee(
    employee_id="noor",
    team_id="intelligence",
    name="Noor",
    identity=EmployeeIdentity(
        first_name="Noor",
        last_name="",
        title="Geopolitical/external risk intelligence",
        specialization="scm_intelligence",
        seniority="Senior",
        background="Expert in Geopolitical/external risk intelligence."
    ),
    reasoning_profile_id="standard"
)
