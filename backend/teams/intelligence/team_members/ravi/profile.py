from workforce.employees.models import Employee, EmployeeIdentity

ravi = Employee(
    employee_id="ravi",
    team_id="intelligence",
    name="Ravi",
    identity=EmployeeIdentity(
        first_name="Ravi",
        last_name="",
        title="Supplier intelligence",
        specialization="scm_intelligence",
        seniority="Senior",
        background="Expert in Supplier intelligence."
    ),
    reasoning_profile_id="standard"
)
