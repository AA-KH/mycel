import importlib
import logging
from typing import Dict, List, Optional, Any
from organization.teams.models import Team
from organization.types import CompanyStatus

logger = logging.getLogger(__name__)

class TeamRegistryError(Exception):
    pass

class TeamRegistry:
    def __init__(self):
        self._teams: Dict[str, Team] = {}

    def register(self, team: Team) -> None:
        if not team.id:
            raise TeamRegistryError("Team must have an ID.")
        if team.id in self._teams:
            raise TeamRegistryError(f"Team {team.id} is already registered.")
        
        self._teams[team.id] = team
        logger.info(f"Registered team: {team.id}")

    def unregister(self, team_id: str) -> None:
        if team_id in self._teams:
            del self._teams[team_id]

    def get_team(self, team_id: str) -> Optional[Team]:
        return self._teams.get(team_id)

    def exists(self, team_id: str) -> bool:
        return team_id in self._teams

    def list_teams(self) -> List[Team]:
        return list(self._teams.values())

    def list_active(self) -> List[Team]:
        return [t for t in self._teams.values() if t.status == CompanyStatus.ACTIVE]

    def get_summary(self, team_id: str) -> Optional[Dict[str, Any]]:
        team = self.get_team(team_id)
        if not team:
            return None
        return {
            "team_id": team.id,
            "display_name": team.name,
            "status": team.status,
            "department_id": team.department_id,
            "position_count": 0, # Stubs for now, would delegate to PositionRegistry
            "member_count": 0,
            "pipeline_count": 0,
            "skill_count": 0,
            "tool_count": 0
        }

    def get_details(self, team_id: str) -> Optional[Dict[str, Any]]:
        team = self.get_team(team_id)
        if not team:
            return None
        return {
            "identity": team.model_dump(),
            "common_skills": self.get_common_skills(team_id),
            "common_tools": self.get_common_tools(team_id),
            "positions": self.get_positions(team_id),
            "members": self.get_members(team_id),
            "pipelines": self.get_pipelines(team_id)
        }

    # Delegate methods (Stubs to represent capability pointers, not deep resolution)
    def get_positions(self, team_id: str) -> List[str]:
        # Would inject PositionRegistry here
        return []

    def get_members(self, team_id: str) -> List[str]:
        # Would inject TeamMemberRegistry here
        return []

    def get_pipelines(self, team_id: str) -> List[str]:
        return []

    def get_common_skills(self, team_id: str) -> List[str]:
        return []

    def get_common_tools(self, team_id: str) -> List[str]:
        return []

class TeamCatalogue:
    """Idempotent loader to discover teams from the filesystem."""
    def __init__(self, registry: TeamRegistry):
        self.registry = registry

    def load_from_directory(self, base_dir: str):
        import os
        from pathlib import Path
        base_path = Path(base_dir)
        if not base_path.exists():
            return
            
        for child in base_path.iterdir():
            if child.is_dir() and (child / "team.py").exists():
                try:
                    # Dynamically import the team module
                    module_name = f"teams.{child.name}.team"
                    spec = importlib.util.spec_from_file_location(module_name, str(child / "team.py"))
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        if hasattr(module, "team_instance"):
                            self.registry.register(module.team_instance)
                except TeamRegistryError as e:
                    logger.error(f"Duplicate or invalid team {child.name}: {e}")
                except Exception as e:
                    logger.error(f"Failed to load team {child.name}: {e}")
