from typing import Dict, Any, Optional
from core.errors import DomainError

from execution.reasoning.strategies import VALID_STRATEGIES
from .registry import TeamReasoningRegistry
from .schemas import ResolvedTeamReasoningResponse, TeamReasoningProfileResponse, StrategyAssignmentResponse

class TeamReasoningResolver:
    """
    Resolves the high-level reasoning methodology for a team, mapping their DB Profile
    to the global statically defined `VALID_STRATEGIES`.
    """
    def __init__(self, registry: TeamReasoningRegistry):
        self.registry = registry

    async def resolve(self, team_id: str) -> Optional[ResolvedTeamReasoningResponse]:
        profile = await self.registry.get_active_profile(team_id)
        if not profile:
            return None
            
        assignments = await self.registry.get_strategy_assignments(profile.id)
        
        # Validate that assignments map to actual code implementations
        resolved_strategies = []
        for assignment in assignments:
            if assignment.strategy_id not in VALID_STRATEGIES:
                # Log warning or gracefully ignore broken strategy references
                continue
                
            resolved_strategies.append(
                StrategyAssignmentResponse(
                    id=assignment.id,
                    strategy_id=assignment.strategy_id,
                    priority=assignment.priority,
                    required=assignment.required,
                    status=assignment.status
                )
            )
            
        # Sort by priority ascending (1 is highest priority)
        resolved_strategies.sort(key=lambda x: x.priority)
        
        return ResolvedTeamReasoningResponse(
            profile=TeamReasoningProfileResponse(**profile.model_dump()),
            strategies=resolved_strategies
        )
