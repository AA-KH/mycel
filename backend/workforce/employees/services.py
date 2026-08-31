"""
Services for the Employee domain.
Validates business rules and lifecycle constraints.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from core.errors import DomainError, NotFoundError
from infrastructure.events.schemas import EventEnvelope
from infrastructure.events.base import BaseEventPublisher

from organization.services import OrganizationService

from .models import Employee, EmployeeStatus, PerformanceSummary
from .repositories import EmployeeRepository
from .schemas import EmployeeCreate, EmployeeUpdate, EmployeeStatusUpdate


class EmployeeService:
    def __init__(
        self,
        employee_repo: EmployeeRepository,
        organization_service: OrganizationService,
        event_publisher: BaseEventPublisher
    ):
        self.employee_repo = employee_repo
        self.org_service = organization_service
        self.event_publisher = event_publisher

    async def _validate_organization_hierarchy(self, company_id: str, dept_id: str, team_id: str, pos_id: str):
        """Ensures that the entire organizational chain is valid and belongs to the specified company."""
        # This will raise NotFoundError if the company doesn't exist
        await self.org_service.get_company(company_id)
        
        dept = await self.org_service.get_department(company_id, dept_id)
        team = await self.org_service.get_team(company_id, team_id)
        pos = await self.org_service.get_position(company_id, pos_id)
        
        if team.department_id != dept.id:
            raise DomainError("Team does not belong to the specified department.")
            
        if pos.team_id != team.id:
            raise DomainError("Position does not belong to the specified team.")

    async def create_employee(self, data: EmployeeCreate) -> Employee:
        # Validate hierarchy and multi-tenancy
        await self._validate_organization_hierarchy(
            company_id=data.company_id,
            dept_id=data.department_id,
            team_id=data.team_id,
            pos_id=data.position_id
        )

        # Validate name uniqueness in company
        if await self.employee_repo.get_by_name(data.company_id, data.name):
            raise DomainError(f"Employee with name '{data.name}' already exists in this company.")

        employee = Employee(**data.model_dump(exclude={"memory_config"}))
        if data.memory_config:
            employee.memory_config = data.memory_config
        
        # Initialize default performance summary
        employee.performance_summary = PerformanceSummary()

        created = await self.employee_repo.create(employee)

        await self._publish_event("employee.created", created.id, created.model_dump(), created.company_id)
        return created

    async def get_employee(self, company_id: str, employee_id: str) -> Employee:
        emp = await self.employee_repo.get_by_id(employee_id)
        if not emp or emp.company_id != company_id:
            raise NotFoundError(f"Employee '{employee_id}' not found in company '{company_id}'")
        return emp

    async def update_employee(self, company_id: str, employee_id: str, data: EmployeeUpdate) -> Employee:
        emp = await self.get_employee(company_id, employee_id)
        
        if emp.status == EmployeeStatus.TERMINATED:
            raise DomainError("Cannot update a terminated employee through standard updates.")

        if data.name and data.name != emp.name:
            if await self.employee_repo.get_by_name(company_id, data.name):
                raise DomainError(f"Employee with name '{data.name}' already exists in this company.")

        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return emp

        update_data["updated_at"] = datetime.now(timezone.utc)
        updated = await self.employee_repo.update(employee_id, update_data)
        
        await self._publish_event("employee.updated", updated.id, updated.model_dump(), company_id)
        return updated

    async def update_status(self, company_id: str, employee_id: str, data: EmployeeStatusUpdate) -> Employee:
        emp = await self.get_employee(company_id, employee_id)

        # State machine logic
        if emp.status == EmployeeStatus.RETIRED and data.status != EmployeeStatus.RETIRED:
            raise DomainError("Cannot revive a retired employee through a status update.")

        if emp.status == data.status:
            return emp

        updated = await self.employee_repo.update(employee_id, {
            "status": data.status,
            "updated_at": datetime.now(timezone.utc)
        })

        await self._publish_event(
            "employee.status_changed", 
            updated.id, 
            {"old_status": emp.status, "new_status": data.status}, 
            company_id
        )
        return updated

    async def list_employees(
        self, 
        company_id: str, 
        department_id: Optional[str] = None, 
        team_id: Optional[str] = None, 
        position_id: Optional[str] = None
    ) -> List[Employee]:
        
        if position_id:
            # Assumes company check already performed inside position fetching if needed,
            # but repository bounds it by company_id anyway.
            return await self.employee_repo.get_all_by_position(company_id, position_id)
        elif team_id:
            return await self.employee_repo.get_all_by_team(company_id, team_id)
        elif department_id:
            return await self.employee_repo.get_all_by_department(company_id, department_id)
        else:
            return await self.employee_repo.get_all_by_company(company_id)

    async def _publish_event(self, event_type: str, entity_id: str, payload: Dict[str, Any], company_id: Optional[str] = None):
        event = EventEnvelope(
            event_type=event_type,
            company_id=company_id,
            payload={"entity_id": entity_id, "data": payload}
        )
        await self.event_publisher.publish(event)
