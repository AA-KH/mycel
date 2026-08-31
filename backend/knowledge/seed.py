import asyncio
import logging
from core.mongodb import mongodb_connection

from organization.teams.repository import TeamRepository
from organization.registry import TeamRegistry

from knowledge.repository import (
    KnowledgeSpaceRepository, KnowledgeSourceRepository, 
    KnowledgeDocumentRepository, KnowledgeChunkRepository
)
from knowledge.registry import KnowledgeRegistry
from knowledge.access import KnowledgeAccessPolicy
from knowledge.ingestion.parser import MockTextParser
from knowledge.ingestion.chunker import ChunkingService
from knowledge.ingestion.service import IngestionService
from knowledge.retrieval.vectorstore import InMemoryVectorStore
from knowledge.retrieval.embedding import MockEmbeddingProvider
from knowledge.retrieval.retriever import KnowledgeRetriever
from knowledge.models import KnowledgeSourceType, TrustLevel, KnowledgeSource, KnowledgeDocument

logger = logging.getLogger(__name__)

async def seed_knowledge():
    """Idempotent seed for Team Knowledge foundation."""
    logger.info("Starting Team Knowledge seed...")
    
    db = mongodb_connection.db
    
    team_repo = TeamRepository(db)
    team_registry = TeamRegistry(team_repo)
    
    space_repo = KnowledgeSpaceRepository(db)
    source_repo = KnowledgeSourceRepository(db)
    doc_repo = KnowledgeDocumentRepository(db)
    chunk_repo = KnowledgeChunkRepository(db)
    
    knowledge_registry = KnowledgeRegistry(space_repo, source_repo, doc_repo, team_registry)
    
    vector_store = InMemoryVectorStore()
    embedding_provider = MockEmbeddingProvider()
    parser = MockTextParser()
    chunker = ChunkingService(chunk_size=100) # Small chunk size for the mock
    
    ingestion_service = IngestionService(
        doc_repo=doc_repo,
        chunk_repo=chunk_repo,
        parser=parser,
        chunker=chunker,
        embedding=embedding_provider,
        vector_store=vector_store
    )

    # 1. Setup Backend Team Space
    backend_team = await team_repo.get_by_id("team-backend")
    if not backend_team:
        logger.info("Team 'team-backend' not found. Skipping knowledge seed.")
        return

    space = await knowledge_registry.get_knowledge_space_by_team(backend_team.id)
    if not space:
        space = await knowledge_registry.create_knowledge_space(
            team_id=backend_team.id,
            name="Backend Engineering Knowledge",
            description="Core engineering documentation and standards."
        )
        logger.info(f"Created KnowledgeSpace {space.id} for team-backend")
    else:
        logger.info(f"KnowledgeSpace {space.id} already exists for team-backend")
        
    # 2. Setup a mock Source
    mock_uri = "mock://internal-docs/coding-standards.txt"
    existing_sources = await source_repo.get_by_space(space.id)
    source = next((s for s in existing_sources if s.uri == mock_uri), None)
    
    if not source:
        source = await source_repo.create(KnowledgeSource(
            knowledge_space_id=space.id,
            name="Backend Coding Standards",
            type=KnowledgeSourceType.INTERNAL_DOCUMENT,
            uri=mock_uri,
            trust_level=TrustLevel.OFFICIAL
        ))
        logger.info(f"Created KnowledgeSource {source.id}")
        
        # 3. Create Document mapping
        doc = await doc_repo.create(KnowledgeDocument(
            source_id=source.id,
            knowledge_space_id=space.id,
            title="Backend Coding Standards"
        ))
        
        # 4. Ingest (Parse -> Chunk -> Embed -> Store)
        await ingestion_service.ingest_document(doc.id, mock_uri)
        logger.info(f"Ingested KnowledgeDocument {doc.id} successfully.")
    else:
        logger.info(f"KnowledgeSource {source.id} already seeded.")
        
    logger.info("Team Knowledge seed complete.")

if __name__ == "__main__":
    asyncio.run(seed_knowledge())
