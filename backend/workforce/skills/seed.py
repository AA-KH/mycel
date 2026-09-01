import asyncio
import logging
from core.mongodb import mongodb_connection
from infrastructure.events.base import BaseEventPublisher
from workforce.skills.repository import SkillRepository, TeamSkillRepository
from workforce.skills.service import SkillService, TeamSkillService
from workforce.skills.schemas import SkillCreate, TeamSkillAssignmentCreate
from workforce.skills.models import SkillImportance
from organization.registry import TeamRegistry
from organization.teams.repository import TeamRepository
from organization.company.repository import CompanyRepository

from teams.developer.common.skills.skills import ENGINEERING_SKILLS
from teams.research.common.skills.skills import RESEARCH_SKILLS
from teams.legal.common.skills.skills import LEGAL_SKILLS
from teams.finance.common.skills.skills import FINANCE_SKILLS
from workforce.skills.shared_catalogue import SHARED_SKILLS

logger = logging.getLogger(__name__)

async def seed_skills():
    """Idempotent seed for the Team Common Skills baseline."""
    logger.info("Starting skills seed...")
    
    db = mongodb_connection.db
    skill_repo = SkillRepository(db)
    team_skill_repo = TeamSkillRepository(db)
    team_repo = TeamRepository(db)
    publisher = BaseEventPublisher()  # Use base or mock publisher if just seeding DB directly
    
    skill_service = SkillService(skill_repo, publisher)
    team_registry = TeamRegistry(team_repo)
    team_skill_service = TeamSkillService(team_skill_repo, skill_service, team_registry, publisher)
    
    # 1. Create all skills
    all_skills = ENGINEERING_SKILLS + RESEARCH_SKILLS + LEGAL_SKILLS + FINANCE_SKILLS + SHARED_SKILLS
    for skill_data in all_skills:
        existing = await skill_repo.get_by_skill_id(skill_data["skill_id"])
        if not existing:
            await skill_service.create(SkillCreate(**skill_data))
            logger.info(f"Created skill: {skill_data['skill_id']}")
        else:
            logger.info(f"Skill already exists: {skill_data['skill_id']}")
            
    # 2. Assign to teams (TOS 1 seed created "team-backend")
    backend_team = await team_repo.get_by_id("team-backend")
    if backend_team:
        logger.info("Assigning engineering skills to backend team...")
        for eng_skill in ENGINEERING_SKILLS:
            try:
                await team_skill_service.assign_skill(
                    backend_team.id,
                    TeamSkillAssignmentCreate(
                        skill_id=eng_skill["skill_id"],
                        importance=SkillImportance.CORE,
                        required=True,
                        proficiency_baseline=80
                    )
                )
                logger.info(f"Assigned {eng_skill['skill_id']} to team-backend")
            except Exception as e:
                if "already assigned" in str(e):
                    logger.info(f"Skill {eng_skill['skill_id']} already assigned to team-backend")
                else:
                    logger.error(f"Error assigning {eng_skill['skill_id']}: {e}")
    else:
        logger.info("Team 'team-backend' not found. Ensure organization seed is run first.")

    logger.info("Skills seed complete.")

if __name__ == "__main__":
    asyncio.run(seed_skills())
