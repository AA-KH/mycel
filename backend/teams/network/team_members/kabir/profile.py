from workforce.employees.models import Employee, EmployeeIdentity

kabir = Employee(
    employee_id="kabir",
    team_id="network",
    name="Kabir",
    identity=EmployeeIdentity(
        first_name="Kabir",
        last_name="",
        title="Logistics & fulfillment",
        specialization="scm_network",
        seniority="Senior",
        background="Expert in Logistics & fulfillment."
    ),
    reasoning_profile_id="standard"
)
