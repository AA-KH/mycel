from workforce.employees.models import Employee, EmployeeIdentity

omar = Employee(
    employee_id="omar",
    team_id="council",
    name="Omar",
    identity=EmployeeIdentity(
        first_name="Omar",
        last_name="",
        title="Risk & Compliance Strategist",
        specialization="scm_council",
        seniority="Senior",
        background="Expert in multi-framework regulatory compliance (GDPR, FCPA, OFAC, ISO 37001, REACH/RoHS), sanctions screening, and enterprise risk governance."
    ),
    reasoning_profile_id="standard"
)
