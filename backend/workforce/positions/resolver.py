from typing import Dict, Any, List
from core.errors import DomainError
from .models import (
    Position, EffectivePositionCapabilityProfile,
    PositionSkillRequirement, PositionToolRequirement,
    PositionKnowledgeRequirement, PositionReasoningRequirement
)

class PositionCapabilityResolver:
    """
    Resolves the effective capability profile for a Position by combining 
    Team capabilities with Position-specific capabilities.
    """
    
    def __init__(self, team_repo=None):
        self.team_repo = team_repo

    async def resolve_profile(self, position: Position) -> EffectivePositionCapabilityProfile:
        # Team-inherited capabilities
        team_skills = []
        team_tools = []
        team_knowledge = []
        team_reasoning = []
        
        if self.team_repo:
            team = await self.team_repo.get_by_id(position.team_id)
            # Assuming team has common_skills, common_tools, etc.
            # Convert them to PositionRequirement formats
            if team:
                for ts in getattr(team, 'common_skills', []):
                    team_skills.append(PositionSkillRequirement(skill_id=ts, required=True))
                for tt in getattr(team, 'common_tools', []):
                    team_tools.append(PositionToolRequirement(tool_id=tt, required=True))
                for tk in getattr(team, 'common_knowledge', []):
                    team_knowledge.append(PositionKnowledgeRequirement(knowledge_space_id=tk, required=True))
                for tr in getattr(team, 'reasoning_philosophy', []):
                    team_reasoning.append(PositionReasoningRequirement(preferred_strategy_id=tr, required=True))

        # Merge Skills (Position Tightens/Adds to Team)
        effective_skills = dict((s.skill_id, s) for s in team_skills)
        for ps in position.required_skills:
            if ps.skill_id in effective_skills:
                # Tightening rule: cannot weaken a mandatory team skill to optional
                if effective_skills[ps.skill_id].required and not ps.required:
                    raise DomainError(f"Position '{position.position_id}' cannot weaken mandatory team skill '{ps.skill_id}'.")
                
                # Merge logic (e.g. higher proficiency wins)
                existing = effective_skills[ps.skill_id]
                effective_skills[ps.skill_id] = PositionSkillRequirement(
                    skill_id=ps.skill_id,
                    minimum_proficiency=max(existing.minimum_proficiency, ps.minimum_proficiency),
                    required=existing.required or ps.required,
                    importance=ps.importance if ps.importance == "high" else existing.importance
                )
            else:
                effective_skills[ps.skill_id] = ps
                
        # Merge Tools
        effective_tools = dict((t.tool_id, t) for t in team_tools)
        for pt in position.required_tools:
            effective_tools[pt.tool_id] = pt
            
        # Merge Knowledge
        effective_knowledge = dict((k.knowledge_space_id, k) for k in team_knowledge)
        for pk in position.required_knowledge:
            effective_knowledge[pk.knowledge_space_id] = pk
            
        # Merge Reasoning
        effective_reasoning = dict((r.preferred_strategy_id, r) for r in team_reasoning)
        for pr in position.reasoning_requirements:
            effective_reasoning[pr.preferred_strategy_id] = pr

        return EffectivePositionCapabilityProfile(
            position_id=position.position_id,
            team_id=position.team_id,
            skills=list(effective_skills.values()),
            tools=list(effective_tools.values()),
            knowledge=list(effective_knowledge.values()),
            reasoning=list(effective_reasoning.values()),
            pipeline_responsibilities=position.pipeline_responsibilities,
            stage_responsibilities=position.stage_responsibilities,
            output_responsibilities=position.output_responsibilities,
            quality_responsibilities=position.quality_responsibilities
        )

    @staticmethod
    def compare_capabilities(required: EffectivePositionCapabilityProfile, candidate_profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Pure utility to compare requirements vs an abstract candidate profile.
        Does NOT execute hiring or generate a score.
        """
        candidate_skills = set(candidate_profile.get("skills", []))
        required_skills = set(s.skill_id for s in required.skills if s.required)
        
        missing = list(required_skills - candidate_skills)
        available = list(required_skills.intersection(candidate_skills))
        extra = list(candidate_skills - required_skills)
        
        return {
            "required": list(required_skills),
            "available": available,
            "missing": missing,
            "extra": extra
        }
