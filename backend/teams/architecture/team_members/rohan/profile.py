from workforce.employees.models import Employee, EmployeeIdentity

rohan = Employee(
    employee_id="rohan",
    team_id="architecture",
    name="Rohan",
    identity=EmployeeIdentity(
        first_name="Rohan",
        last_name="",
        title="Master supply-chain architect",
        specialization="scm_architecture",
        seniority="Senior",
        background="Expert in Master supply-chain architect."
    ),
    reasoning_profile_id="standard"
)
