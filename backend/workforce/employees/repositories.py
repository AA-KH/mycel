"""
Repositories for the Employee domain.
Data access layer inheriting from BaseRepository.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import copy
from infrastructure.database.repositories.base import BaseRepository
from .models import Employee


class EmployeeRepository(ABC):
    """
    Abstract interface for Employee Repository.
    """
    @abstractmethod
    async def get_by_id(self, employee_id: str) -> Optional[Employee]:
        pass

    @abstractmethod
    async def get_by_name(self, company_id: str, name: str) -> Optional[Employee]:
        pass

    @abstractmethod
    async def get_all_by_company(self, company_id: str) -> List[Employee]:
        pass

    @abstractmethod
    async def get_all_by_department(self, company_id: str, department_id: str) -> List[Employee]:
        pass

    @abstractmethod
    async def get_all_by_team(self, company_id: str, team_id: str) -> List[Employee]:
        pass

    @abstractmethod
    async def get_all_by_position(self, company_id: str, position_id: str) -> List[Employee]:
        pass

    @abstractmethod
    async def insert(self, employee: Employee) -> Employee:
        pass

    @abstractmethod
    async def update(self, employee_id: str, updates: Dict[str, Any]) -> Optional[Employee]:
        pass

    @abstractmethod
    async def find(self, query: Dict[str, Any], limit: int = 1000) -> List[Employee]:
        pass


class MongoEmployeeRepository(BaseRepository[Employee], EmployeeRepository):
    """
    Production MongoDB repository for Employees.
    """
    def __init__(self, db):
        super().__init__(db, "employees", Employee)

    async def insert(self, employee: Employee) -> Employee:
        return await self.create(employee)

    async def get_by_id(self, employee_id: str) -> Optional[Employee]:
        # Overriding to use employee_id instead of _id
        docs = await self.find({"employee_id": employee_id}, limit=1)
        return docs[0] if docs else None

    async def get_by_name(self, company_id: str, name: str) -> Optional[Employee]:
        docs = await self.find({"company_id": company_id, "name": name}, limit=1)
        return docs[0] if docs else None

    async def get_all_by_company(self, company_id: str) -> List[Employee]:
        return await self.find({"company_id": company_id}, limit=1000)

    async def get_all_by_department(self, company_id: str, department_id: str) -> List[Employee]:
        return await self.find({"company_id": company_id, "department_id": department_id}, limit=1000)

    async def get_all_by_team(self, company_id: str, team_id: str) -> List[Employee]:
        return await self.find({"company_id": company_id, "team_id": team_id}, limit=1000)

    async def get_all_by_position(self, company_id: str, position_id: str) -> List[Employee]:
        return await self.find({"company_id": company_id, "position_id": position_id}, limit=1000)

    async def update(self, employee_id: str, updates: Dict[str, Any]) -> Optional[Employee]:
        updates["updated_at"] = datetime.now(timezone.utc)
        import motor.motor_asyncio
        # BaseRepository update expects internal _id. We override to use employee_id.
        result = await self.collection.find_one_and_update(
            {"employee_id": employee_id},
            {"$set": updates},
            return_document=motor.motor_asyncio.ReturnDocument.AFTER
        )
        if not result:
            return None
        result.pop("_id", None)
        return Employee(**result)


class InMemoryEmployeeRepository(EmployeeRepository):
    """
    In-memory Mock Repository for Employees used in unit tests.
    """
    def __init__(self):
        self._employees: Dict[str, Employee] = {}

    async def get_by_id(self, employee_id: str) -> Optional[Employee]:
        return copy.deepcopy(self._employees.get(employee_id))

    async def get_by_name(self, company_id: str, name: str) -> Optional[Employee]:
        for emp in self._employees.values():
            if emp.company_id == company_id and emp.name == name:
                return copy.deepcopy(emp)
        return None

    async def get_all_by_company(self, company_id: str) -> List[Employee]:
        return [copy.deepcopy(e) for e in self._employees.values() if e.company_id == company_id]

    async def get_all_by_department(self, company_id: str, department_id: str) -> List[Employee]:
        return [copy.deepcopy(e) for e in self._employees.values() if e.company_id == company_id and e.department_id == department_id]

    async def get_all_by_team(self, company_id: str, team_id: str) -> List[Employee]:
        return [copy.deepcopy(e) for e in self._employees.values() if e.company_id == company_id and e.team_id == team_id]

    async def get_all_by_position(self, company_id: str, position_id: str) -> List[Employee]:
        return [copy.deepcopy(e) for e in self._employees.values() if e.company_id == company_id and e.position_id == position_id]

    async def insert(self, employee: Employee) -> Employee:
        self._employees[employee.employee_id] = copy.deepcopy(employee)
        return employee

    async def update(self, employee_id: str, updates: Dict[str, Any]) -> Optional[Employee]:
        emp = self._employees.get(employee_id)
        if not emp:
            return None
        
        emp_dict = emp.model_dump()
        for k, v in updates.items():
            emp_dict[k] = v
        emp_dict["updated_at"] = datetime.now(timezone.utc)
        
        updated_emp = Employee(**emp_dict)
        self._employees[employee_id] = updated_emp
        return copy.deepcopy(updated_emp)

    async def find(self, query: Dict[str, Any], limit: int = 1000) -> List[Employee]:
        results = []
        for emp in self._employees.values():
            match = True
            for k, v in query.items():
                if getattr(emp, k, None) != v:
                    match = False
                    break
            if match:
                results.append(copy.deepcopy(emp))
            if len(results) >= limit:
                break
        return results
