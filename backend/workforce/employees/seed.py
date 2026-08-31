import asyncio
import logging
from typing import List
from workforce.employees.models import Employee
from workforce.employees.repositories import EmployeeRepository
from workforce.employees.validators import EmployeeDefinitionValidator
from teams.developer.team_members.emp_kabir_sharma.profile import kabir
from teams.research.team_members.emp_aarav_mehta.profile import aarav
from teams.creative.team_members.emp_riya_sharma.profile import riya

CATALOGUE_EMPLOYEES = [kabir, aarav, riya]

logger = logging.getLogger(__name__)

class EmployeeSeeder:
    def __init__(self, repository: EmployeeRepository):
        self.repository = repository

    async def seed(self, employees: List[Employee] = None) -> None:
        """
        Idempotent operation to seed or update the employee catalogue.
        """
        if employees is None:
            employees = CATALOGUE_EMPLOYEES

        for emp in employees:
            try:
                # 1. Validate the definition
                EmployeeDefinitionValidator.validate(emp)
                
                # 2. Check if exists
                existing = await self.repository.get_by_id(emp.employee_id)
                
                if existing:
                    # Update
                    # We merge the fields from the catalogue definition
                    updates = emp.model_dump(exclude={"created_at", "updated_at"})
                    await self.repository.update(emp.employee_id, updates)
                    logger.info(f"Updated employee: {emp.employee_id}")
                else:
                    # Insert
                    await self.repository.insert(emp)
                    logger.info(f"Seeded new employee: {emp.employee_id}")
                    
            except Exception as e:
                logger.error(f"Failed to seed employee {emp.employee_id}: {e}")
                
if __name__ == "__main__":
    from motor.motor_asyncio import AsyncIOMotorClient
    from core.config import settings
    from workforce.employees.repositories import MongoEmployeeRepository
    
    async def main():
        client = AsyncIOMotorClient(settings.MONGODB_URI)
        db = client[settings.MONGODB_DB_NAME]
        repo = MongoEmployeeRepository(db)
        seeder = EmployeeSeeder(repo)
        await seeder.seed()
        print("Seeding completed.")
        
    asyncio.run(main())
