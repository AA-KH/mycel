from core.errors import DomainError
from .models import Position

class PositionValidator:
    """
    Validates structural integrity and cross-references of a Position.
    Requires passing in the various registries if reference checks are needed.
    """
    
    def __init__(self, 
                 team_registry=None,
                 skill_registry=None, 
                 tool_registry=None,
                 knowledge_registry=None,
                 reasoning_registry=None,
                 pipeline_registry=None,
                 stage_definition_registry=None,
                 output_contract_registry=None,
                 quality_gate_registry=None):
        self.team_registry = team_registry
        self.skill_registry = skill_registry
        self.tool_registry = tool_registry
        self.knowledge_registry = knowledge_registry
        self.reasoning_registry = reasoning_registry
        self.pipeline_registry = pipeline_registry
        self.stage_definition_registry = stage_definition_registry
        self.output_contract_registry = output_contract_registry
        self.quality_gate_registry = quality_gate_registry

    async def validate_position(self, position: Position):
        if not position.position_id:
            raise DomainError("position_id is required.")
        if not position.team_id:
            raise DomainError("team_id is required.")
            
        # Optional cross-reference checks
        if self.team_registry:
            team = await self.team_registry.get_team(position.team_id)
            if not team:
                raise DomainError(f"Team '{position.team_id}' does not exist.")
            
            # Check for weakening mandatory team skills
            team_mandatory_skills = {ts for ts in getattr(team, 'common_skills', [])}
            for ps in position.required_skills:
                if ps.skill_id in team_mandatory_skills and not ps.required:
                    raise DomainError(f"Position '{position.position_id}' cannot weaken mandatory team skill '{ps.skill_id}'.")
                
        if self.skill_registry:
            for req in position.required_skills:
                skill = await self.skill_registry.get_skill(req.skill_id)
                if not skill:
                    raise DomainError(f"Referenced skill '{req.skill_id}' does not exist.")
                    
        if self.tool_registry:
            for req in position.required_tools:
                tool = await self.tool_registry.get_tool(req.tool_id)
                if not tool:
                    raise DomainError(f"Referenced tool '{req.tool_id}' does not exist.")
                    
        if self.stage_definition_registry:
            for stage_id in position.stage_responsibilities:
                stage = await self.stage_definition_registry.get_definition(stage_id)
                if not stage:
                    raise DomainError(f"Referenced stage definition '{stage_id}' does not exist.")
                    
        if self.output_contract_registry:
            for out_id in position.output_responsibilities:
                contract = await self.output_contract_registry.get_contract(out_id)
                if not contract:
                    raise DomainError(f"Referenced output contract '{out_id}' does not exist.")
                    
        if self.pipeline_registry:
            for pipe_id in position.pipeline_responsibilities:
                pipeline = await self.pipeline_registry.get_pipeline(pipe_id)
                if not pipeline:
                    raise DomainError(f"Referenced pipeline '{pipe_id}' does not exist.")
                
                # Verify team ownership boundary
                # Position belongs to Team A, but references Team B's pipeline without permission?
                # For TOS 10, strict isolation requires pipeline team matches position team
                if pipeline.team_id != position.team_id:
                    raise DomainError(f"Position '{position.position_id}' belongs to team '{position.team_id}' but references pipeline '{pipe_id}' from team '{pipeline.team_id}'.")
