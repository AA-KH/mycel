from workforce.employees.models import Employee, EmployeeIdentity

atlas = Employee(
    employee_id="atlas",
    team_id="executive",
    name="Atlas",
    identity=EmployeeIdentity(
        first_name="Atlas",
        last_name="",
        title="Chief Supply Chain Architect / orchestration",
        specialization="scm_executive",
        seniority="Senior",
        background="Expert in Chief Supply Chain Architect / orchestration."
    ),
    reasoning_profile_id="standard"
)
