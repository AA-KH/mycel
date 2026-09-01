from workforce.employees.models import Employee, EmployeeIdentity

sofia = Employee(
    employee_id="sofia",
    team_id="council",
    name="Sofia",
    identity=EmployeeIdentity(
        first_name="Sofia",
        last_name="",
        title="Council Chair",
        specialization="scm_council",
        seniority="Executive",
        background="Strategic integrator and final decision-maker. Synthesizes recommendations from Cost, Resilience, Operations, and Compliance perspectives into binding Council resolutions."
    ),
    reasoning_profile_id="standard"
)
