import importlib
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class BaselineMemberCatalogue:
    def __init__(self, registry):
        self.registry = registry

    async def load_all(self, teams_dir: Path):
        for team_dir in teams_dir.iterdir():
            if not team_dir.is_dir() or team_dir.name.startswith("__"):
                continue
                
            baseline_dir = team_dir / "team_members" / "baseline"
            if not baseline_dir.exists():
                continue
                
            for py_file in baseline_dir.glob("*.py"):
                if py_file.name == "__init__.py":
                    continue
                    
                module_path = f"teams.{team_dir.name}.team_members.baseline.{py_file.stem}"
                try:
                    module = importlib.import_module(module_path)
                    for attr_name in dir(module):
                        if attr_name.startswith("__"):
                            continue
                        obj = getattr(module, attr_name)
                        if hasattr(obj, "baseline_member_id"):
                            await self.registry.register_baseline(obj)
                except Exception as e:
                    logger.error(f"Failed to load baseline {module_path}: {e}")
