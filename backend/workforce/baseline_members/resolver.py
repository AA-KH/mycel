from typing import Dict, Any
from workforce.baseline_members.models import BaselineMember
from workforce.positions.models import Position

class BaselineCapabilityResolver:
    def __init__(self, team_registry=None):
        self.team_registry = team_registry

    async def resolve_capabilities(self, position: Position) -> Dict[str, Any]:
        """
        Resolves Team Common + Position = Baseline Profile.
        Returns a dictionary representing the minimum expected loadout.
        """
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
