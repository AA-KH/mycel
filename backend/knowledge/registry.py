from typing import Optional
from core.errors import DomainError

from knowledge.repository import KnowledgeSpaceRepository, KnowledgeSourceRepository, KnowledgeDocumentRepository
from knowledge.models import KnowledgeSpace, KnowledgeSource, KnowledgeDocument
from organization.registry import TeamRegistry


class KnowledgeRegistry:
    def __init__(
        self,
        space_repo: KnowledgeSpaceRepository,
        source_repo: KnowledgeSourceRepository,
        doc_repo: KnowledgeDocumentRepository,
        team_registry: TeamRegistry
    ):
        self.space_repo = space_repo
        self.source_repo = source_repo
        self.doc_repo = doc_repo
        self.team_registry = team_registry

    async def get_knowledge_space_by_team(self, team_id: str) -> Optional[KnowledgeSpace]:
        """Returns the default knowledge space for a team, if it exists."""
        return await self.space_repo.get_by_team(team_id)

    async def create_knowledge_space(self, team_id: str, name: str, description: str = "") -> KnowledgeSpace:
        # Validate team exists
        await self.team_registry.resolve_team_identity(team_id)
        
        existing = await self.get_knowledge_space_by_team(team_id)
        if existing:
            raise DomainError(f"KnowledgeSpace already exists for team '{team_id}'")
            
        space = KnowledgeSpace(
            team_id=team_id,
            name=name,
            description=description
        )
        return await self.space_repo.create(space)

    async def get_source(self, source_id: str) -> Optional[KnowledgeSource]:
        return await self.source_repo.get_by_id(source_id)

    async def get_document(self, document_id: str) -> Optional[KnowledgeDocument]:
        return await self.doc_repo.get_by_id(document_id)
