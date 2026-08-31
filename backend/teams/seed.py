import importlib
import logging
from pathlib import Path
from typing import Dict, List, Any
from organization.teams.models import Team
from execution.pipelines.models import TeamPipeline
from workforce.employees.models import Employee

logger = logging.getLogger(__name__)

class TeamCatalogueSeed:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        
    def load_teams(self) -> List[Team]:
        teams = []
        for child in self.base_dir.iterdir():
            if child.is_dir() and (child / "team.py").exists():
                try:
                    mod_path = f"teams.{child.name}.team"
                    spec = importlib.util.spec_from_file_location(mod_path, str(child / "team.py"))
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    teams.append(mod.team_instance)
                except Exception as e:
                    logger.error(f"Failed to load team {child.name}: {e}")
        return teams

    def load_pipelines(self) -> List[TeamPipeline]:
        pipelines = []
        for team_dir in self.base_dir.iterdir():
            if not team_dir.is_dir(): continue
            pipe_dir = team_dir / "pipelines"
            if not pipe_dir.exists(): continue
            
            for pipe_file in pipe_dir.glob("*.py"):
                if pipe_file.name == "__init__.py": continue
                try:
                    mod_path = f"teams.{team_dir.name}.pipelines.{pipe_file.stem}"
                    spec = importlib.util.spec_from_file_location(mod_path, str(pipe_file))
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    pipelines.append(mod.pipeline_instance)
                except Exception as e:
                    pass
        return pipelines

    def load_members(self) -> List[Employee]:
        members = []
        for team_dir in self.base_dir.iterdir():
            if not team_dir.is_dir(): continue
            mem_dir = team_dir / "team_members"
            if not mem_dir.exists(): continue
            
            for mem_file in mem_dir.glob("*/profile.py"):
                try:
                    emp_dir = mem_file.parent.name
                    mod_path = f"teams.{team_dir.name}.team_members.{emp_dir}.profile"
                    spec = importlib.util.spec_from_file_location(mod_path, str(mem_file))
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    
                    # Find any Employee instance exported in this module
                    for attr_name in dir(mod):
                        if attr_name.startswith("__"): continue
                        attr = getattr(mod, attr_name)
                        if isinstance(attr, Employee):
                            members.append(attr)
                            break
                except Exception as e:
                    pass
            
            # Load from subdirectories
            for sub_dir in mem_dir.iterdir():
                if sub_dir.is_dir() and sub_dir.name not in ("__pycache__", "baseline"):
                    try:
                        mod_path = f"teams.{team_dir.name}.team_members.{sub_dir.name}"
                        mod = importlib.import_module(mod_path)
                        if hasattr(mod, "member_instance"):
                            members.append(mod.member_instance)
                    except Exception as e:
                        pass
        return members

def seed():
    # Deterministic loading of the entire catalogue
    base = Path(__file__).parent
    seeder = TeamCatalogueSeed(base)
    
    teams = seeder.load_teams()
    pipelines = seeder.load_pipelines()
    members = seeder.load_members()
    
    return {
        "teams": teams,
        "pipelines": pipelines,
        "members": members
    }
