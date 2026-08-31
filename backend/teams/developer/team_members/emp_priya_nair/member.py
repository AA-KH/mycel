from workforce.employees.models import (
    Employee, EmployeeStatus, EmployeeAvailability
)
from .identity import identity, personality
from .skills import skills
from .tools import tools, permissions
from .specialization import specialization, reasoning_profile_id

member_instance = Employee(
    employee_id="emp_dev_lead_001",
    company_id="mycel_global",
    department_id="default",
    team_id="developer",
    position_id="lead_developer",
    name="Priya Nair",
    display_name="Priya Nair",
    identity=identity,
    personality=personality,
    experience=specialization,
    skills=skills,
    tools=tools,
    permissions=permissions,
    reasoning_profile_id=reasoning_profile_id,
    status=EmployeeStatus.ACTIVE,
    availability=EmployeeAvailability.AVAILABLE
)
