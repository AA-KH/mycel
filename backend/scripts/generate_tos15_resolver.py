import os
from pathlib import Path

BACKEND_DIR = Path("d:/Projects/agent-virtual-office/backend")
TEAMS_DIR = BACKEND_DIR / "teams"
CAPABILITIES_DIR = TEAMS_DIR / "capabilities"
TESTS_DIR = BACKEND_DIR / "tests" / "teams"

MODELS_CONTENT = """from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone

class TeamCapabilityProfile(BaseModel):
    team_id: str
    team_version: str = "1.0.0"
    
    skills: List[str] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)
    knowledge: List[str] = Field(default_factory=list)
    reasoning: List[str] = Field(default_factory=list)
    
    pipelines: List[str] = Field(default_factory=list)
    stages: List[str] = Field(default_factory=list)
    outputs: List[str] = Field(default_factory=list)
    quality_requirements: List[str] = Field(default_factory=list)
    
    positions: List[str] = Field(default_factory=list)
    
    workforce_summary: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    resolved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TeamCapabilityResolutionResult(BaseModel):
    team_id: str
    profile: Optional[TeamCapabilityProfile] = None
    resolved: bool = False
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    resolved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
"""

RESOLVER_CONTENT = """import logging
from typing import Dict, List, Optional, Any
from teams.capabilities.models import TeamCapabilityProfile, TeamCapabilityResolutionResult
from teams.registry import TeamRegistry
from execution.pipelines.registry import PipelineRegistry

logger = logging.getLogger(__name__)

class TeamCapabilityResolver:
    def __init__(self, team_registry: TeamRegistry, pipeline_registry: PipelineRegistry):
        self.team_registry = team_registry
        self.pipeline_registry = pipeline_registry

    def resolve(self, team_id: str, strict: bool = False) -> TeamCapabilityResolutionResult:
        result = TeamCapabilityResolutionResult(team_id=team_id)
        
        team = self.team_registry.get_team(team_id)
        if not team:
            result.errors.append(f"Team {team_id} does not exist in TeamRegistry.")
            if strict:
                return result
            
        profile = TeamCapabilityProfile(team_id=team_id)
        
        # 1. Resolve TeamRegistry Accessors (Skills, Tools, etc.)
        if team:
            try:
                profile.skills = self.team_registry.get_common_skills(team_id)
                profile.tools = self.team_registry.get_common_tools(team_id)
                profile.positions = self.team_registry.get_positions(team_id)
                # In a real implementation, Knowledge and Reasoning would also be fetched here.
                # Since get_common_knowledge is not in TOS 13's contract, we stub them.
                profile.knowledge = []
                profile.reasoning = []
            except Exception as e:
                msg = f"Failed resolving core capabilities: {e}"
                result.errors.append(msg)
                if strict: return result
                else: result.warnings.append(msg)
        
        # 2. Resolve Pipeline Capabilities
        try:
            pipelines = self.pipeline_registry.get_team_pipelines(team_id)
            for pipe in pipelines:
                profile.pipelines.append(pipe.pipeline_id)
                if pipe.output_contract_id:
                    profile.outputs.append(pipe.output_contract_id)
                    
                profile.quality_requirements.extend(pipe.pipeline_gate_ids)
                
                for stage in pipe.stages:
                    profile.stages.append(stage.stage_id)
        except Exception as e:
            msg = f"Failed resolving pipelines: {e}"
            result.errors.append(msg)
            if strict: return result
            else: result.warnings.append(msg)
            
        # Deduplicate
        profile.skills = list(set(profile.skills))
        profile.tools = list(set(profile.tools))
        profile.outputs = list(set(profile.outputs))
        profile.stages = list(set(profile.stages))
        profile.quality_requirements = list(set(profile.quality_requirements))
        
        result.profile = profile
        result.resolved = len(result.errors) == 0
        
        return result

    def has_skill(self, team_id: str, skill_id: str) -> bool:
        res = self.resolve(team_id)
        return res.resolved and skill_id in res.profile.skills

    def has_tool(self, team_id: str, tool_id: str) -> bool:
        res = self.resolve(team_id)
        return res.resolved and tool_id in res.profile.tools
        
    def has_knowledge(self, team_id: str, knowledge_id: str) -> bool:
        res = self.resolve(team_id)
        return res.resolved and knowledge_id in res.profile.knowledge
        
    def has_pipeline(self, team_id: str, pipeline_id: str) -> bool:
        res = self.resolve(team_id)
        return res.resolved and pipeline_id in res.profile.pipelines
        
    def supports_output(self, team_id: str, output_type: str) -> bool:
        res = self.resolve(team_id)
        return res.resolved and output_type in res.profile.outputs
        
    def has_position(self, team_id: str, position_id: str) -> bool:
        res = self.resolve(team_id)
        return res.resolved and position_id in res.profile.positions

    def matches_requirements(self, team_id: str, requirements: Dict[str, List[str]]) -> Dict[str, Any]:
        \"\"\"
        Primitive for Future Task Routing.
        requirements format: {"skills": ["python"], "outputs": ["video"]}
        \"\"\"
        res = self.resolve(team_id)
        if not res.resolved or not res.profile:
            return {"matched": False, "missing": ["team_resolution_failed"]}
            
        prof = res.profile
        missing = []
        
        for req_skill in requirements.get("skills", []):
            if req_skill not in prof.skills:
                missing.append(f"skill:{req_skill}")
                
        for req_tool in requirements.get("tools", []):
            if req_tool not in prof.tools:
                missing.append(f"tool:{req_tool}")
                
        for req_out in requirements.get("outputs", []):
            if req_out not in prof.outputs:
                missing.append(f"output:{req_out}")
                
        return {
            "matched": len(missing) == 0,
            "missing": missing
        }
"""

TESTS_CONTENT = """import pytest
from teams.capabilities.models import TeamCapabilityProfile, TeamCapabilityResolutionResult
from teams.resolver import TeamCapabilityResolver
from teams.registry import TeamRegistry
from execution.pipelines.registry import PipelineRegistry
from organization.teams.models import Team
from execution.pipelines.models import TeamPipeline, PipelineInputContract

# Mocking the accessor behavior
class MockTeamRegistry(TeamRegistry):
    def get_common_skills(self, team_id: str) -> list[str]:
        if team_id == "developer": return ["programming", "api_development"]
        if team_id == "creative": return ["design", "video_editing"]
        return []
    def get_common_tools(self, team_id: str) -> list[str]:
        if team_id == "developer": return ["github", "terminal"]
        return []
    def get_positions(self, team_id: str) -> list[str]:
        if team_id == "developer": return ["backend_engineer"]
        return []

@pytest.fixture
def registry_setup():
    tr = MockTeamRegistry()
    tr.register(Team(id="developer", company_id="global", name="Dev", slug="dev"))
    tr.register(Team(id="creative", company_id="global", name="Creative", slug="cr"))
    
    pr = PipelineRegistry(tr)
    # Developer Pipeline
    pipe1 = TeamPipeline(
        pipeline_id="developer_main",
        team_id="developer",
        name="main",
        display_name="Main Pipeline",
        input_contract=PipelineInputContract(input_type="task"),
        output_contract_id="backend_service",
        stages=[]
    )
    # Creative Pipeline
    pipe2 = TeamPipeline(
        pipeline_id="creative_main",
        team_id="creative",
        name="main",
        display_name="Main Pipeline",
        input_contract=PipelineInputContract(input_type="task"),
        output_contract_id="promotional_video",
        stages=[]
    )
    pr.register(pipe1)
    pr.register(pipe2)
    
    return tr, pr

@pytest.fixture
def resolver(registry_setup):
    tr, pr = registry_setup
    return TeamCapabilityResolver(tr, pr)

def test_team_resolution(resolver):
    res = resolver.resolve("developer")
    assert res.resolved is True
    assert "programming" in res.profile.skills
    assert "github" in res.profile.tools
    assert "developer_main" in res.profile.pipelines
    assert "backend_service" in res.profile.outputs
    assert "backend_engineer" in res.profile.positions

def test_team_isolation(resolver):
    res = resolver.resolve("developer")
    # Dev should not have creative properties
    assert "design" not in res.profile.skills
    assert "creative_main" not in res.profile.pipelines
    assert "promotional_video" not in res.profile.outputs

def test_missing_team(resolver):
    res = resolver.resolve("finance", strict=True)
    assert res.resolved is False
    assert len(res.errors) > 0

def test_matches_requirements(resolver):
    # Match Success
    reqs1 = {"skills": ["programming"], "outputs": ["backend_service"]}
    match1 = resolver.matches_requirements("developer", reqs1)
    assert match1["matched"] is True
    assert len(match1["missing"]) == 0
    
    # Match Fail
    reqs2 = {"skills": ["programming", "quantum_computing"], "outputs": ["backend_service"]}
    match2 = resolver.matches_requirements("developer", reqs2)
    assert match2["matched"] is False
    assert "skill:quantum_computing" in match2["missing"]

def test_architectural_compliance():
    resolver = TeamCapabilityResolver(None, None)
    assert not hasattr(resolver, "call_llm")
    assert not hasattr(resolver, "create_agent")
    assert not hasattr(resolver, "execute_tool")
    assert not hasattr(resolver, "execute_stage")
    assert not hasattr(resolver, "hire_member")
"""

def generate_resolver():
    CAPABILITIES_DIR.mkdir(parents=True, exist_ok=True)
    init_file = CAPABILITIES_DIR / "__init__.py"
    if not init_file.exists():
        init_file.write_text("")
    
    models_file = CAPABILITIES_DIR / "models.py"
    models_file.write_text(MODELS_CONTENT, encoding="utf-8")
    
    resolver_file = TEAMS_DIR / "resolver.py"
    resolver_file.write_text(RESOLVER_CONTENT, encoding="utf-8")
    
    TESTS_DIR.mkdir(parents=True, exist_ok=True)
    test_file = TESTS_DIR / "test_team_resolver.py"
    test_file.write_text(TESTS_CONTENT, encoding="utf-8")

if __name__ == "__main__":
    generate_resolver()
    print("Generated TOS 15 Team Capability Resolver.")
