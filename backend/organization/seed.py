import asyncio
import logging
from .company.repository import CompanyRepository
from .departments.repository import DepartmentRepository
from .teams.repository import TeamRepository
from .positions.repository import PositionRepository
from .company.models import Company
from .departments.models import Department
from .teams.models import Team
from .positions.models import Position
from .types import CompanyStatus, Level, PositionRequirements, CapabilityRequirement
from core.mongodb import mongodb_connection

logger = logging.getLogger(__name__)

async def seed_organization():
    """Minimal idempotent seed for testing/development."""
    logger.info("Starting organization seed...")
    
    company_repo = CompanyRepository(mongodb_connection.db)
    dept_repo = DepartmentRepository(mongodb_connection.db)
    team_repo = TeamRepository(mongodb_connection.db)
    pos_repo = PositionRepository(mongodb_connection.db)
    
    # 1. Company
    company_slug = "mycel"
    company = await company_repo.get_by_slug(company_slug)
    if not company:
        company = Company(
            id="mycel",
            name="Mycel",
            slug=company_slug,
            description="Agent Virtual Office",
            status=CompanyStatus.ACTIVE
        )
        company = await company_repo.create(company)
        logger.info(f"Created company: {company.name}")
    else:
        logger.info(f"Company {company_slug} already exists.")
        
    # 2. Department
    dept_slug = "engineering"
    dept = await dept_repo.get_by_slug(company.id, dept_slug)
    if not dept:
        dept = Department(
            id="dept-eng",
            company_id=company.id,
            name="Engineering",
            slug=dept_slug,
            description="Engineering Department",
            status=CompanyStatus.ACTIVE
        )
        dept = await dept_repo.create(dept)
        logger.info(f"Created department: {dept.name}")
    else:
        logger.info(f"Department {dept_slug} already exists.")
        
    # 3. Team
    team_slug = "backend-engineering"
    team = await team_repo.get_by_slug(company.id, team_slug)
    if not team:
        team = Team(
            id="team-backend",
            company_id=company.id,
            department_id=dept.id,
            name="Backend Engineering",
            slug=team_slug,
            description="Core backend systems",
            status=CompanyStatus.ACTIVE
        )
        team = await team_repo.create(team)
        logger.info(f"Created team: {team.name}")
    else:
        logger.info(f"Team {team_slug} already exists.")
        
    # 4. Position
    pos_slug = "backend-engineer"
    pos = await pos_repo.get_by_slug(company.id, pos_slug)
    if not pos:
        pos = Position(
            id="pos-backend",
            company_id=company.id,
            department_id=dept.id,
            team_id=team.id,
            title="Backend Engineer",
            slug=pos_slug,
            description="Python backend specialist",
            level=Level.MID,
            status="open",
            responsibilities=["API Development"],
            requirements=PositionRequirements(capabilities=[
                CapabilityRequirement(capability="python", minimum_level=80)
            ])
        )
        pos = await pos_repo.create(pos)
        logger.info(f"Created position: {pos.title}")
    else:
        logger.info(f"Position {pos_slug} already exists.")

    logger.info("Organization seed complete.")

if __name__ == "__main__":
    asyncio.run(seed_organization())
