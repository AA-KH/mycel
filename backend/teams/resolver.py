import logging
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
        """
        Primitive for Future Task Routing.
        requirements format: {"skills": ["python"], "outputs": ["video"]}
        """
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
