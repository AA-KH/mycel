import uuid
from datetime import datetime, timezone
from typing import Optional

from knowledge.models import KnowledgeDocument, DocumentStatus, KnowledgeChunk
from knowledge.repository import KnowledgeDocumentRepository, KnowledgeChunkRepository
from knowledge.retrieval.vectorstore import VectorStore
from knowledge.retrieval.embedding import EmbeddingProvider
from knowledge.ingestion.parser import DocumentParser
from knowledge.ingestion.chunker import ChunkingService

class IngestionService:
    """
    Orchestrates the pipeline: 
    Parse -> Chunk -> Embed -> Store -> Update Document Status
    """
    def __init__(
        self,
        doc_repo: KnowledgeDocumentRepository,
        chunk_repo: KnowledgeChunkRepository,
        parser: DocumentParser,
        chunker: ChunkingService,
        embedding: EmbeddingProvider,
        vector_store: VectorStore
    ):
        self.doc_repo = doc_repo
        self.chunk_repo = chunk_repo
        self.parser = parser
        self.chunker = chunker
        self.embedding = embedding
        self.vector_store = vector_store

    async def ingest_document(self, document_id: str, uri: str) -> KnowledgeDocument:
        """Synchronous ingestion for TOS 4 foundation."""
        doc = await self.doc_repo.get_by_id(document_id)
        if not doc:
            raise ValueError("Document not found")
            
        if doc.status in (DocumentStatus.INDEXED, DocumentStatus.PROCESSING):
            return doc # Already processing/done
            
        # 1. Mark Processing
        doc = await self.doc_repo.update(document_id, {"status": DocumentStatus.PROCESSING})
        
        try:
            # 2. Parse Text
            text = await self.parser.parse(uri)
            
            # 3. Chunk
            text_chunks = await self.chunker.chunk_text(text)
            
            # 4. Embed & Store
            position = 0
            for text_chunk in text_chunks:
                chunk_id = str(uuid.uuid4())
                
                # Create domain model
                chunk = KnowledgeChunk(
                    id=chunk_id,
                    document_id=document_id,
                    knowledge_space_id=doc.knowledge_space_id,
                    content=text_chunk,
                    position=position,
                    token_count=len(text_chunk.split()), # rough estimation
                    metadata={"source_uri": uri, "title": doc.title}
                )
                await self.chunk_repo.create(chunk)
                
                # Embed
                vector = await self.embedding.embed_text(text_chunk)
                
                # Upsert to Vector Store
                await self.vector_store.upsert(
                    knowledge_space_id=doc.knowledge_space_id,
                    chunk_id=chunk_id,
                    document_id=document_id,
                    vector=vector,
                    content=text_chunk,
                    metadata=chunk.metadata
                )
                position += 1
                
            # 5. Mark Indexed
            doc = await self.doc_repo.update(document_id, {
                "status": DocumentStatus.INDEXED,
                "indexed_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            })
            return doc
            
        except Exception as e:
            # Mark Failed
            doc = await self.doc_repo.update(document_id, {
                "status": DocumentStatus.FAILED,
                "metadata": {"error": str(e)},
                "updated_at": datetime.now(timezone.utc)
            })
            raise e
