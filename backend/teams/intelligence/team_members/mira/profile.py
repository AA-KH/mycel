from workforce.employees.models import Employee, EmployeeIdentity

mira = Employee(
    employee_id="mira",
    team_id="intelligence",
    name="Mira",
    identity=EmployeeIdentity(
        first_name="Mira",
        last_name="",
        title="Market & demand intelligence",
        specialization="scm_intelligence",
        seniority="Senior",
        background="Expert in Market & demand intelligence."
    ),
    reasoning_profile_id="standard"
)
