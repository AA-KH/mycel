from fastapi import Depends
from api.dependencies.core import DbDep, EventPublisherDep
from api.dependencies.organization import get_team_repository

from workforce.skills.repository import SkillRepository, TeamSkillRepository
from workforce.skills.service import SkillService, TeamSkillService
from workforce.skills.registry import SkillRegistry, TeamSkillRegistry
from organization.registry import TeamRegistry

def get_skill_repository(db: DbDep) -> SkillRepository:
    return SkillRepository(db)

def get_team_skill_repository(db: DbDep) -> TeamSkillRepository:
    return TeamSkillRepository(db)

def get_skill_service(
    publisher: EventPublisherDep,
    repo: SkillRepository = Depends(get_skill_repository)
) -> SkillService:
    return SkillService(repo, publisher)

def get_team_registry_dep(
    team_repo = Depends(get_team_repository)
) -> TeamRegistry:
    return TeamRegistry(team_repo)

def get_team_skill_service(
    publisher: EventPublisherDep,
    team_skill_repo: TeamSkillRepository = Depends(get_team_skill_repository),
    skill_service: SkillService = Depends(get_skill_service),
    team_registry: TeamRegistry = Depends(get_team_registry_dep)
) -> TeamSkillService:
    return TeamSkillService(team_skill_repo, skill_service, team_registry, publisher)

def get_skill_registry(repo: SkillRepository = Depends(get_skill_repository)) -> SkillRegistry:
    return SkillRegistry(repo)

def get_team_skill_registry(repo: TeamSkillRepository = Depends(get_team_skill_repository)) -> TeamSkillRegistry:
    return TeamSkillRegistry(repo)
