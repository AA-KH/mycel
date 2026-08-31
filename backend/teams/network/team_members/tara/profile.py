from workforce.employees.models import Employee, EmployeeIdentity

tara = Employee(
    employee_id="tara",
    team_id="network",
    name="Tara",
    identity=EmployeeIdentity(
        first_name="Tara",
        last_name="",
        title="Inventory & capacity planning",
        specialization="scm_network",
        seniority="Senior",
        background="Expert in Inventory & capacity planning."
    ),
    reasoning_profile_id="standard"
)
