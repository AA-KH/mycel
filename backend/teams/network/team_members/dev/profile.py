from workforce.employees.models import Employee, EmployeeIdentity

dev = Employee(
    employee_id="dev",
    team_id="network",
    name="Dev",
    identity=EmployeeIdentity(
        first_name="Dev",
        last_name="",
        title="Procurement & total landed cost",
        specialization="scm_network",
        seniority="Senior",
        background="Expert in Procurement & total landed cost."
    ),
    reasoning_profile_id="standard"
)
