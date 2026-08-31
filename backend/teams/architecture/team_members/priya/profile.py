from workforce.employees.models import Employee, EmployeeIdentity

priya = Employee(
    employee_id="priya",
    team_id="architecture",
    name="Priya",
    identity=EmployeeIdentity(
        first_name="Priya",
        last_name="",
        title="Implementation planner",
        specialization="scm_architecture",
        seniority="Senior",
        background="Expert in Implementation planner."
    ),
    reasoning_profile_id="standard"
)
