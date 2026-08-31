"""
Employee Registry.
Provides a unified view and resolution mechanism for Employee definitions.
Acts as a high-level facade over the repository.
"""

from typing import List, Optional, Dict, Any
from core.errors import NotFoundError
from .models import Employee, EmployeeStatus, EmployeeAvailability
from .repositories import EmployeeRepository

class EmployeeRegistry:
    def __init__(self, employee_repo: EmployeeRepository):
        self.employee_repo = employee_repo

    async def get_active_employee(self, company_id: str, employee_id: str) -> Employee:
        """Fetch an employee and ensure they are active and ready for work."""
        emp = await self.employee_repo.get_by_id(employee_id)
        if not emp or emp.company_id != company_id:
            raise NotFoundError(f"Employee '{employee_id}' not found.")
        
        if emp.status != EmployeeStatus.ACTIVE:
            raise ValueError(f"Employee '{employee_id}' is not currently active. Status: {emp.status}")
            
        return emp

    async def resolve_by_role(self, company_id: str, role_title: str) -> Optional[Employee]:
        """
        Temporary resolution mechanism for mapping legacy roles to an actual employee.
        """
        employees = await self.employee_repo.get_all_by_company(company_id)
        for emp in employees:
            if emp.status == EmployeeStatus.ACTIVE:
                if role_title.lower() in emp.identity.title.lower():
                    return emp
        return None

    # --- Phase 8: Capability Discovery Querie ---
    
    async def find_by_skill(self, company_id: str, skill_id: str, min_proficiency: int = 0) -> List[Employee]:
        """Find active employees possessing a specific skill at or above a proficiency level."""
        active = await self.find_active(company_id)
        results = []
        for emp in active:
            skill = emp.skills.get(skill_id)
            if skill and skill.level >= min_proficiency:
                results.append(emp)
        return results

    async def find_by_tool(self, company_id: str, tool_id: str) -> List[Employee]:
        """Find active employees who have access to a specific tool."""
        active = await self.find_active(company_id)
        return [emp for emp in active if tool_id in emp.tools]

    async def find_by_output(self, company_id: str, output_type: str) -> List[Employee]:
        """Find active employees capable of producing a specific output type."""
        active = await self.find_active(company_id)
        return [emp for emp in active if output_type in emp.outputs]

    async def find_active(self, company_id: str) -> List[Employee]:
        """Return all employees in ACTIVE status for a company."""
        return await self.employee_repo.find({"company_id": company_id, "status": EmployeeStatus.ACTIVE})

    async def get_capability_snapshot(self, company_id: str) -> List[Dict[str, Any]]:
        """
        Generate a normalized capability snapshot of all active employees.
        This provides the foundational candidate pool input for Phase 9 (Smart Hiring).
        """
        active = await self.find_active(company_id)
        snapshots = []
        for emp in active:
            snapshots.append({
                "employee_id": emp.employee_id,
                "name": emp.name,
                "position_id": emp.position_id,
                "specialization": emp.identity.specialization,
                "reasoning_profile_id": emp.reasoning_profile_id,
                "skills": {s_name: s.level for s_name, s in emp.skills.items()},
                "tools": emp.tools,
                "outputs": emp.outputs,
                "status": emp.status.value,
                "availability": emp.availability.value
            })
        return snapshots
