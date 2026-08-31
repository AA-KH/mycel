from typing import List, Optional
from infrastructure.database.repositories.base import BaseRepository
from .models import KnowledgeSpace, KnowledgeSource, KnowledgeDocument, KnowledgeChunk

class KnowledgeSpaceRepository(BaseRepository[KnowledgeSpace]):
    def __init__(self, db):
        super().__init__(db, "knowledge_spaces", KnowledgeSpace)
        
    async def get_by_team(self, team_id: str) -> Optional[KnowledgeSpace]:
        docs = await self.find({"team_id": team_id}, limit=1)
        return docs[0] if docs else None

class KnowledgeSourceRepository(BaseRepository[KnowledgeSource]):
    def __init__(self, db):
        super().__init__(db, "knowledge_sources", KnowledgeSource)
        
    async def get_by_space(self, space_id: str) -> List[KnowledgeSource]:
        return await self.find({"knowledge_space_id": space_id}, limit=1000)

class KnowledgeDocumentRepository(BaseRepository[KnowledgeDocument]):
    def __init__(self, db):
        super().__init__(db, "knowledge_documents", KnowledgeDocument)
        
    async def get_by_source(self, source_id: str) -> List[KnowledgeDocument]:
        return await self.find({"source_id": source_id}, limit=1000)
        
    async def get_by_checksum(self, space_id: str, checksum: str) -> Optional[KnowledgeDocument]:
        docs = await self.find({"knowledge_space_id": space_id, "checksum": checksum}, limit=1)
        return docs[0] if docs else None

class KnowledgeChunkRepository(BaseRepository[KnowledgeChunk]):
    def __init__(self, db):
        super().__init__(db, "knowledge_chunks", KnowledgeChunk)
        
    async def get_by_document(self, document_id: str) -> List[KnowledgeChunk]:
        return await self.find({"document_id": document_id}, limit=10000)
