import asyncio
import os
import sys
from datetime import datetime, timezone

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.mongodb import mongodb_connection
from infrastructure.events.publisher import event_publisher

from organization.repositories import (
    CompanyRepository,
    DepartmentRepository,
    TeamRepository,
    PositionRepository,
)
from organization.services import OrganizationService

from workforce.employees.models import (
    Employee,
    EmployeeStatus,
    EmployeeIdentity,
    Personality,
    PersonalityTraits,
    Experience,
    SkillProficiency,
    ReasoningProfile,
    ToolPermission,
    MemoryConfig,
    PerformanceSummary
)
from workforce.employees.repositories import EmployeeRepository
from workforce.employees.services import EmployeeService


async def main():
    print("Connecting to MongoDB...")
    await mongodb_connection.connect()

    db = mongodb_connection.db

    # Initialize Services
    org_service = OrganizationService(
        company_repo=CompanyRepository(db),
        dept_repo=DepartmentRepository(db),
        team_repo=TeamRepository(db),
        position_repo=PositionRepository(db),
        event_publisher=event_publisher
    )

    employee_repo = EmployeeRepository(db)
    employee_service = EmployeeService(
        employee_repo=employee_repo,
        organization_service=org_service,
        event_publisher=event_publisher
    )

    # 1. Fetch Mycel company and organization tree to attach employees
    try:
        company = await org_service.get_company_by_slug("mycel")
        if not company:
            print("Company 'mycel' not found. Please run seed_company.py first.")
            return

        dept = await org_service.get_department_by_slug(company.id, "engineering")
        frontend_team = await org_service.get_team_by_slug(company.id, "frontend")
        backend_team = await org_service.get_team_by_slug(company.id, "backend")
        
        # In seed_company.py we created a position for "Lead Frontend Engineer" and "Backend Architect"
        # Let's query positions to bind our employees.
        positions = await org_service.position_repo.get_all_by_team(company.id, frontend_team.id)
        frontend_pos = positions[0] if positions else None
        
        positions = await org_service.position_repo.get_all_by_team(company.id, backend_team.id)
        backend_pos = positions[0] if positions else None

        if not frontend_pos or not backend_pos:
            print("Required positions not found. Please run seed_company.py first.")
            return

        print(f"Using Company: {company.name}")

        # Seed Employees
        employees_data = [
            {
                "company_id": company.id,
                "department_id": dept.id,
                "team_id": frontend_team.id,
                "position_id": frontend_pos.id,
                "name": "Riya Sharma",
                "display_name": "Riya",
                "identity": EmployeeIdentity(
                    title="Lead Frontend Engineer",
                    summary="Passionate about pixel-perfect UI and component architecture.",
                    personality="Creative and expressive",
                    communication_style="Enthusiastic and collaborative",
                    experience_level="Senior"
                ),
                "personality": Personality(
                    traits=PersonalityTraits(analytical=60, creative=95, cautious=40, proactive=85),
                    communication_style="Enthusiastic",
                    decision_style="Design-first"
                ),
                "experience": Experience(
                    level="Senior",
                    years_equivalent=7,
                    domains=["frontend", "ui/ux", "web animations"]
                ),
                "skills": {
                    "react": SkillProficiency(level=98, experience="Expert"),
                    "css": SkillProficiency(level=95, experience="Expert"),
                    "ui_design": SkillProficiency(level=88, experience="Advanced")
                },
                "reasoning_profile": ReasoningProfile(
                    strategy="design_implement_review",
                    planning_depth="medium",
                    verification_required=True,
                    critique_required=False
                ),
                "tools": ["browser.open", "figma.read", "github.commit"],
                "permissions": {
                    "browser.open": ToolPermission.ALLOWED,
                    "github.commit": ToolPermission.ALLOWED
                }
            },
            {
                "company_id": company.id,
                "department_id": dept.id,
                "team_id": backend_team.id,
                "position_id": backend_pos.id,
                "name": "Kabir Singh",
                "display_name": "Kabir",
                "identity": EmployeeIdentity(
                    title="Backend Architect",
                    summary="Focuses on scalability, database optimization, and solid system architecture.",
                    personality="Analytical and serious",
                    communication_style="Concise and technical",
                    experience_level="Staff"
                ),
                "personality": Personality(
                    traits=PersonalityTraits(analytical=98, creative=40, cautious=90, proactive=80),
                    communication_style="Concise",
                    decision_style="Data-driven"
                ),
                "experience": Experience(
                    level="Staff",
                    years_equivalent=10,
                    domains=["backend architecture", "databases", "distributed systems"]
                ),
                "skills": {
                    "python": SkillProficiency(level=96, experience="Expert"),
                    "mongodb": SkillProficiency(level=92, experience="Expert"),
                    "system_design": SkillProficiency(level=95, experience="Expert")
                },
                "reasoning_profile": ReasoningProfile(
                    strategy="plan_validate_execute",
                    planning_depth="deep",
                    verification_required=True,
                    critique_required=True
                ),
                "tools": ["terminal.execute", "database.query", "github.commit"],
                "permissions": {
                    "terminal.execute": ToolPermission.APPROVAL_REQUIRED,
                    "database.query": ToolPermission.ALLOWED
                }
            }
        ]

        print("Seeding employees...")
        for edata in employees_data:
            existing = await employee_repo.get_by_name(company.id, edata["name"])
            if not existing:
                emp = Employee(**edata)
                await employee_repo.create(emp)
                print(f"Created employee: {emp.name} ({emp.identity.title})")
            else:
                print(f"Employee {edata['name']} already exists.")

    finally:
        await mongodb_connection.close()
        print("Done.")

if __name__ == "__main__":
    asyncio.run(main())
