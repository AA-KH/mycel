from workforce.employees.models import Employee, EmployeeIdentity

leena = Employee(
    employee_id="leena",
    team_id="resilience",
    name="Leena",
    identity=EmployeeIdentity(
        first_name="Leena",
        last_name="",
        title="Supply Chain Stress Tester",
        specialization="scm_resilience",
        seniority="Senior",
        background="Expert in structural stress testing, identifying capacity bottlenecks, and mathematical supply chain breaking points."
    ),
    reasoning_profile_id="standard"
)
