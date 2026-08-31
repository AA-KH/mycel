from fastapi import Depends
from api.dependencies.core import DbDep
from api.dependencies.organization import get_team_repository
from organization.registry import TeamRegistry

from knowledge.repository import (
    KnowledgeSpaceRepository, KnowledgeSourceRepository, 
    KnowledgeDocumentRepository, KnowledgeChunkRepository
)
from knowledge.registry import KnowledgeRegistry
from knowledge.access import KnowledgeAccessPolicy
from knowledge.retrieval.vectorstore import VectorStore, InMemoryVectorStore
from knowledge.retrieval.embedding import EmbeddingProvider, MockEmbeddingProvider
from knowledge.retrieval.retriever import KnowledgeRetriever
from knowledge.ingestion.parser import DocumentParser, MockTextParser
from knowledge.ingestion.chunker import ChunkingService
from knowledge.ingestion.service import IngestionService

# Singleton instances for in-memory mocks
_vector_store = InMemoryVectorStore()
_embedding_provider = MockEmbeddingProvider()
_parser = MockTextParser()
_chunker = ChunkingService()

def get_space_repo(db: DbDep) -> KnowledgeSpaceRepository:
    return KnowledgeSpaceRepository(db)

def get_source_repo(db: DbDep) -> KnowledgeSourceRepository:
    return KnowledgeSourceRepository(db)

def get_document_repo(db: DbDep) -> KnowledgeDocumentRepository:
    return KnowledgeDocumentRepository(db)

def get_chunk_repo(db: DbDep) -> KnowledgeChunkRepository:
    return KnowledgeChunkRepository(db)

def get_team_registry_dep(team_repo = Depends(get_team_repository)) -> TeamRegistry:
    return TeamRegistry(team_repo)

def get_knowledge_registry(
    space_repo: KnowledgeSpaceRepository = Depends(get_space_repo),
    source_repo: KnowledgeSourceRepository = Depends(get_source_repo),
    doc_repo: KnowledgeDocumentRepository = Depends(get_document_repo),
    team_registry: TeamRegistry = Depends(get_team_registry_dep)
) -> KnowledgeRegistry:
    return KnowledgeRegistry(space_repo, source_repo, doc_repo, team_registry)

def get_knowledge_access_policy(
    registry: KnowledgeRegistry = Depends(get_knowledge_registry)
) -> KnowledgeAccessPolicy:
    return KnowledgeAccessPolicy(registry)

def get_vector_store() -> VectorStore:
    return _vector_store

def get_embedding_provider() -> EmbeddingProvider:
    return _embedding_provider

def get_knowledge_retriever(
    registry: KnowledgeRegistry = Depends(get_knowledge_registry),
    vector_store: VectorStore = Depends(get_vector_store),
    embedding: EmbeddingProvider = Depends(get_embedding_provider)
) -> KnowledgeRetriever:
    return KnowledgeRetriever(registry, vector_store, embedding)

def get_ingestion_service(
    doc_repo: KnowledgeDocumentRepository = Depends(get_document_repo),
    chunk_repo: KnowledgeChunkRepository = Depends(get_chunk_repo),
    vector_store: VectorStore = Depends(get_vector_store),
    embedding: EmbeddingProvider = Depends(get_embedding_provider)
) -> IngestionService:
    return IngestionService(doc_repo, chunk_repo, _parser, _chunker, embedding, vector_store)
