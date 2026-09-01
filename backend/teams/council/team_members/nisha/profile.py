from workforce.employees.models import Employee, EmployeeIdentity

nisha = Employee(
    employee_id="nisha",
    team_id="council",
    name="Nisha",
    identity=EmployeeIdentity(
        first_name="Nisha",
        last_name="",
        title="Operations Strategist",
        specialization="scm_council",
        seniority="Senior",
        background="Expert in operational efficiency auditing, OEE analysis, throughput optimization, and translating strategic decisions into executable operational plans."
    ),
    reasoning_profile_id="standard"
)
