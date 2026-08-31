import os
from pathlib import Path

BACKEND_DIR = Path("d:/Projects/agent-virtual-office/backend")
BASELINE_DIR = BACKEND_DIR / "workforce" / "baseline_members"

def ensure_dir(d):
    d.mkdir(parents=True, exist_ok=True)
    init_file = d / "__init__.py"
    if not init_file.exists():
        init_file.write_text("")

ensure_dir(BASELINE_DIR)

models_content = """from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class BaselineStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"

class BaselineSkillProficiency(BaseModel):
    level: int = Field(ge=0, le=100)

class BaselineMember(BaseModel):
    \"\"\"
    The canonical template for a Team Position.
    Represents the minimum expected worker before individual specialization.
    \"\"\"
    baseline_member_id: str
    team_id: str
    position_id: str
    
    display_name: str
    description: str
    
    status: BaselineStatus = BaselineStatus.ACTIVE
    baseline_version: str = "1.0.0"
    
    skills: Dict[str, BaselineSkillProficiency] = Field(default_factory=dict)
    tools: List[str] = Field(default_factory=list)
    knowledge: List[str] = Field(default_factory=list)
    
    reasoning_profile: Optional[str] = None
    
    pipeline_responsibilities: List[str] = Field(default_factory=list)
    stage_responsibilities: List[str] = Field(default_factory=list)
    output_responsibilities: List[str] = Field(default_factory=list)
    quality_responsibilities: List[str] = Field(default_factory=list)
    
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
"""
(BASELINE_DIR / "models.py").write_text(models_content, encoding="utf-8")

repo_content = """from typing import List, Optional
from workforce.baseline_members.models import BaselineMember, BaselineStatus

class BaselineMemberRepository:
    def __init__(self):
        # In-memory storage for now, simulating MongoDB
        self._members = {}
        
    async def create(self, member: BaselineMember) -> BaselineMember:
        key = f"{member.baseline_member_id}_{member.baseline_version}"
        if key in self._members:
            raise ValueError(f"Baseline Member {key} already exists")
        self._members[key] = member
        return member

    async def get_by_baseline_id(self, baseline_member_id: str, version: Optional[str] = None) -> Optional[BaselineMember]:
        if version:
            return self._members.get(f"{baseline_member_id}_{version}")
        
        # Return the most recent/active version
        matches = [m for m in self._members.values() if m.baseline_member_id == baseline_member_id]
        if not matches:
            return None
            
        active = [m for m in matches if m.status == BaselineStatus.ACTIVE]
        return active[0] if active else matches[-1]

    async def get_by_team(self, team_id: str) -> List[BaselineMember]:
        return [m for m in self._members.values() if m.team_id == team_id and m.status == BaselineStatus.ACTIVE]
        
    async def get_by_position(self, position_id: str) -> List[BaselineMember]:
        return [m for m in self._members.values() if m.position_id == position_id and m.status == BaselineStatus.ACTIVE]

    async def get_all_active(self) -> List[BaselineMember]:
        return [m for m in self._members.values() if m.status == BaselineStatus.ACTIVE]

    async def find(self, query: dict, limit: int = 100) -> List[BaselineMember]:
        results = []
        for m in self._members.values():
            match = True
            for k, v in query.items():
                if "." in k:
                    # Simple nested dict check for tools/skills lists
                    field, subfield = k.split(".", 1)
                    val = getattr(m, field, None)
                    if isinstance(val, list) and v not in val:
                        match = False
                    elif isinstance(val, dict) and v not in val:
                        match = False
                else:
                    if getattr(m, k, None) != v:
                        match = False
            if match:
                results.append(m)
                if len(results) >= limit:
                    break
        return results
"""
(BASELINE_DIR / "repository.py").write_text(repo_content, encoding="utf-8")

registry_content = """from typing import List, Optional
from core.errors import DomainError
from workforce.baseline_members.models import BaselineMember
from workforce.baseline_members.repository import BaselineMemberRepository

class BaselineMemberRegistry:
    def __init__(self, repository: BaselineMemberRepository):
        self.repository = repository
        self._validators = []
        
    def add_validator(self, validator):
        self._validators.append(validator)

    async def register_baseline(self, member: BaselineMember) -> BaselineMember:
        for validator in self._validators:
            await validator.validate_baseline(member)
            
        try:
            return await self.repository.create(member)
        except ValueError as e:
            raise DomainError(str(e))

    async def get(self, baseline_member_id: str) -> Optional[BaselineMember]:
        return await self.repository.get_by_baseline_id(baseline_member_id)

    async def get_version(self, baseline_member_id: str, version: str) -> Optional[BaselineMember]:
        return await self.repository.get_by_baseline_id(baseline_member_id, version)
        
    async def get_by_team(self, team_id: str) -> List[BaselineMember]:
        return await self.repository.get_by_team(team_id)
        
    async def get_by_position(self, position_id: str) -> List[BaselineMember]:
        return await self.repository.get_by_position(position_id)

    async def get_active(self) -> List[BaselineMember]:
        return await self.repository.get_all_active()

    async def find_by_skill(self, skill_id: str) -> List[BaselineMember]:
        return await self.repository.find({"skills.skill_id": skill_id, "status": "active"})

    async def find_by_tool(self, tool_id: str) -> List[BaselineMember]:
        return await self.repository.find({"tools": tool_id, "status": "active"})

    async def find_by_pipeline(self, pipeline_id: str) -> List[BaselineMember]:
        return await self.repository.find({"pipeline_responsibilities": pipeline_id, "status": "active"})

    async def find_by_output(self, output_id: str) -> List[BaselineMember]:
        return await self.repository.find({"output_responsibilities": output_id, "status": "active"})
"""
(BASELINE_DIR / "registry.py").write_text(registry_content, encoding="utf-8")

validator_content = """from core.errors import DomainError
from workforce.baseline_members.models import BaselineMember

class BaselineMemberValidator:
    def __init__(
        self,
        team_registry=None,
        position_registry=None,
        skill_registry=None,
        tool_registry=None
    ):
        self.team_registry = team_registry
        self.position_registry = position_registry
        self.skill_registry = skill_registry
        self.tool_registry = tool_registry

    async def validate_baseline(self, member: BaselineMember):
        if self.team_registry:
            team = await self.team_registry.get_team(member.team_id)
            if not team:
                raise DomainError(f"Team '{member.team_id}' does not exist.")
                
        if self.position_registry:
            pos = await self.position_registry.get(member.position_id)
            if not pos:
                raise DomainError(f"Position '{member.position_id}' does not exist.")
            if pos.team_id != member.team_id:
                raise DomainError(f"Position '{member.position_id}' does not belong to Team '{member.team_id}'.")
                
            # Prevent weakening mandatory capabilities
            if self.team_registry:
                team = await self.team_registry.get_team(member.team_id)
                if team:
                    team_skills = {ts for ts in getattr(team, 'common_skills', [])}
                    for ts in team_skills:
                        if ts not in member.skills:
                            raise DomainError(f"Baseline Member cannot weaken mandatory team skill '{ts}'.")
                            
        if self.skill_registry:
            for skill_id in member.skills.keys():
                skill = await self.skill_registry.get_skill(skill_id)
                if not skill:
                    raise DomainError(f"Referenced skill '{skill_id}' does not exist.")
                    
        if self.tool_registry:
            for tool_id in member.tools:
                tool = await self.tool_registry.get_tool(tool_id)
                if not tool:
                    raise DomainError(f"Referenced tool '{tool_id}' does not exist.")
"""
(BASELINE_DIR / "validator.py").write_text(validator_content, encoding="utf-8")

resolver_content = """from typing import Dict, Any
from workforce.baseline_members.models import BaselineMember
from workforce.positions.models import Position

class BaselineCapabilityResolver:
    def __init__(self, team_registry=None):
        self.team_registry = team_registry

    async def resolve_capabilities(self, position: Position) -> Dict[str, Any]:
        \"\"\"
        Resolves Team Common + Position = Baseline Profile.
        Returns a dictionary representing the minimum expected loadout.
        \"\"\"
        skills = {}
        tools = set()
        knowledge = set()
        reasoning = None
        pipelines = set()
        outputs = set()
        quality = set()

        if self.team_registry:
            team = await self.team_registry.get_team(position.team_id)
            if team:
                for s in getattr(team, 'common_skills', []):
                    skills[s] = {"level": 70}
                tools.update(getattr(team, 'common_tools', []))
                knowledge.update(getattr(team, 'knowledge_space', []))
                reasoning = getattr(team, 'reasoning_philosophy', None)
                pipelines.update(getattr(team, 'pipelines', []))

        # Add Position specific
        for s in getattr(position, 'required_skills', []):
            # Upsert or update level
            level = getattr(s, 'minimum_proficiency', 70)
            skills[s.skill_id] = {"level": level}
            
        for t in getattr(position, 'required_tools', []):
            tools.add(t.tool_id)
            
        for k in getattr(position, 'knowledge_requirements', []):
            knowledge.add(k.knowledge_id)
            
        if getattr(position, 'reasoning_requirements', None):
            reasoning = position.reasoning_requirements
            
        pipelines.update(getattr(position, 'pipeline_responsibilities', []))
        outputs.update(getattr(position, 'output_responsibilities', []))
        
        return {
            "skills": skills,
            "tools": list(tools),
            "knowledge": list(knowledge),
            "reasoning_profile": reasoning,
            "pipeline_responsibilities": list(pipelines),
            "output_responsibilities": list(outputs),
            "quality_responsibilities": list(quality)
        }
"""
(BASELINE_DIR / "resolver.py").write_text(resolver_content, encoding="utf-8")

catalogue_content = """import importlib
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
"""
(BASELINE_DIR / "catalogue.py").write_text(catalogue_content, encoding="utf-8")

print("Created baseline domain files.")
