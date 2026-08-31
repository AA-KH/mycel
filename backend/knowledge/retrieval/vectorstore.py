from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class VectorSearchResult(BaseModel):
    chunk_id: str
    document_id: str
    content: str
    score: float
    metadata: Dict[str, Any]

class VectorStore(ABC):
    @abstractmethod
    async def upsert(self, knowledge_space_id: str, chunk_id: str, document_id: str, vector: List[float], content: str, metadata: Dict[str, Any]):
        pass

    @abstractmethod
    async def similarity_search(self, knowledge_space_id: str, query_vector: List[float], top_k: int = 5) -> List[VectorSearchResult]:
        pass

class InMemoryVectorStore(VectorStore):
    """
    A simple in-memory vector store for testing and isolation validation.
    Strictly enforces knowledge_space_id boundaries.
    """
    def __init__(self):
        # space_id -> list of records
        self._store: Dict[str, List[Dict[str, Any]]] = {}

    async def upsert(self, knowledge_space_id: str, chunk_id: str, document_id: str, vector: List[float], content: str, metadata: Dict[str, Any]):
        if knowledge_space_id not in self._store:
            self._store[knowledge_space_id] = []
            
        # In a real store we'd update if it exists. For memory, we just append.
        self._store[knowledge_space_id].append({
            "chunk_id": chunk_id,
            "document_id": document_id,
            "vector": vector,
            "content": content,
            "metadata": metadata
        })

    async def similarity_search(self, knowledge_space_id: str, query_vector: List[float], top_k: int = 5) -> List[VectorSearchResult]:
        # CRITICAL ISOLATION RULE: If the space doesn't exist, return empty.
        # This guarantees Team A cannot see Team B's vectors because they are physically
        # partitioned in memory by the knowledge_space_id key.
        if knowledge_space_id not in self._store:
            return []
            
        records = self._store[knowledge_space_id]
        
        results = []
        for r in records:
            # Mock cosine similarity: just a dummy score for testing
            score = 0.95
            results.append(VectorSearchResult(
                chunk_id=r["chunk_id"],
                document_id=r["document_id"],
                content=r["content"],
                score=score,
                metadata=r["metadata"]
            ))
            
        return results[:top_k]
