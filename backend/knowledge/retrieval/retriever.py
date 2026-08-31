import uuid
from typing import List, Optional
from core.errors import DomainError

from knowledge.models import KnowledgeContext, KnowledgeReference
from knowledge.registry import KnowledgeRegistry
from .vectorstore import VectorStore
from .embedding import EmbeddingProvider

class KnowledgeRetriever:
    """
    Coordinates the secure retrieval of knowledge for a specific Team.
    """
    def __init__(self, registry: KnowledgeRegistry, vector_store: VectorStore, embedding: EmbeddingProvider):
        self.registry = registry
        self.vector_store = vector_store
        self.embedding = embedding

    async def retrieve(self, team_id: str, query: str, top_k: int = 5) -> KnowledgeContext:
        """
        Retrieves context using the Team's authorized KnowledgeSpace.
        This enforces cross-team isolation natively.
        """
        # 1. Resolve team to knowledge space. 
        # This will fail if the team doesn't have a space, guaranteeing safety.
        space = await self.registry.get_knowledge_space_by_team(team_id)
        if not space:
            # Return empty context if no space exists
            return KnowledgeContext(
                team_id=team_id,
                query=query,
                references=[],
                retrieved_chunks=[],
                retrieval_metadata={"status": "no_knowledge_space"}
            )
            
        if space.status != "active":
            raise DomainError("Team knowledge space is archived or disabled.")
            
        # 2. Embed the query
        query_vector = await self.embedding.embed_text(query)
        
        # 3. Search the vector store, strictly scoped to the space_id
        results = await self.vector_store.similarity_search(space.id, query_vector, top_k=top_k)
        
        # 4. Construct RAG Context
        references = []
        chunks = []
        
        for r in results:
            ref = KnowledgeReference(
                knowledge_reference_id=str(uuid.uuid4()),
                document_id=r.document_id,
                chunk_id=r.chunk_id,
                knowledge_space_id=space.id,
                title=r.metadata.get("title", "Unknown"),
                source=r.metadata.get("source_uri", "Unknown"),
                relevance_score=r.score,
                citation_metadata={"position": r.metadata.get("position", 0)}
            )
            references.append(ref)
            
            chunks.append({
                "chunk_id": r.chunk_id,
                "content": r.content
            })
            
        return KnowledgeContext(
            team_id=team_id,
            query=query,
            references=references,
            retrieved_chunks=chunks,
            retrieval_metadata={"space_id": space.id, "total_found": len(results)}
        )
