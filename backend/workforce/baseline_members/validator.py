from core.errors import DomainError
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
