from workforce.employees.models import Employee, EmployeeIdentity

vikram = Employee(
    employee_id="vikram",
    team_id="council",
    name="Vikram",
    identity=EmployeeIdentity(
        first_name="Vikram",
        last_name="",
        title="Resilience strategist",
        specialization="scm_council",
        seniority="Senior",
        background="Expert in Resilience strategist."
    ),
    reasoning_profile_id="standard"
)
