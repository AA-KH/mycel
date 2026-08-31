from workforce.employees.models import Employee, EmployeeIdentity

ethan = Employee(
    employee_id="ethan",
    team_id="architecture",
    name="Ethan",
    identity=EmployeeIdentity(
        first_name="Ethan",
        last_name="",
        title="Independent validator",
        specialization="scm_architecture",
        seniority="Senior",
        background="Expert in Independent validator."
    ),
    reasoning_profile_id="standard"
)
