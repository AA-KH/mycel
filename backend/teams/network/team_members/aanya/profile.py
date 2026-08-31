from workforce.employees.models import Employee, EmployeeIdentity

aanya = Employee(
    employee_id="aanya",
    team_id="network",
    name="Aanya",
    identity=EmployeeIdentity(
        first_name="Aanya",
        last_name="",
        title="Supply-chain network design",
        specialization="scm_network",
        seniority="Senior",
        background="Expert in Supply-chain network design."
    ),
    reasoning_profile_id="standard"
)
