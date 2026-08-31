from typing import Optional
from core.errors import DomainError
from .registry import KnowledgeRegistry

class KnowledgeAccessPolicy:
    """
    Enforces access rules for Knowledge Retrieval.
    Default TOS 4 Rule: A Team can only access its own explicitly defined KnowledgeSpace.
    """
    def __init__(self, registry: KnowledgeRegistry):
        self.registry = registry
        
    async def resolve_authorized_space(self, team_id: str, requested_space_id: Optional[str] = None) -> str:
        """
        Returns the `knowledge_space_id` that this team is authorized to search.
        Rejects cross-team access.
        """
        space = await self.registry.get_knowledge_space_by_team(team_id)
        if not space or space.status != "active":
            raise DomainError(f"Team '{team_id}' has no active KnowledgeSpace.")
            
        # For TOS 4, we strictly enforce that the requested space (if provided) matches the team's space.
        # This prevents Team A from querying Team B's space simply by providing Team B's space ID.
        if requested_space_id and requested_space_id != space.id:
            raise DomainError("Unauthorized: Cross-team knowledge access is denied.")
            
        return space.id
