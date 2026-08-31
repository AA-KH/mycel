from workforce.employees.models import Employee, EmployeeStatus, EmployeeAvailability
from .identity import identity, personality
from .skills import skills
from .tools import tools, permissions
from .specialization import specialization, reasoning_profile_id

member_instance = Employee(
    employee_id="emp_fin_budget_001",
    company_id="mycel_global",
    department_id="default",
    team_id="finance",
    position_id="budget_analyst",
    name="Vikram Mehta",
    display_name="Vikram Mehta",
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
