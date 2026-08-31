from workforce.employees.models import Employee, EmployeeIdentity

anika = Employee(
    employee_id="anika",
    team_id="intelligence",
    name="Anika",
    identity=EmployeeIdentity(
        first_name="Anika",
        last_name="",
        title="Industry & supply-chain benchmarking",
        specialization="scm_intelligence",
        seniority="Senior",
        background="Expert in Industry & supply-chain benchmarking."
    ),
    reasoning_profile_id="standard"
)
