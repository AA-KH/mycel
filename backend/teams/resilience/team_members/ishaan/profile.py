from workforce.employees.models import Employee, EmployeeIdentity

ishaan = Employee(
    employee_id="ishaan",
    team_id="resilience",
    name="Ishaan",
    identity=EmployeeIdentity(
        first_name="Ishaan",
        last_name="",
        title="Disruption scenario generation",
        specialization="scm_resilience",
        seniority="Senior",
        background="Expert in Disruption scenario generation."
    ),
    reasoning_profile_id="standard"
)
