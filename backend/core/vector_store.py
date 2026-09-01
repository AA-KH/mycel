import faiss
import numpy as np
import logging
from typing import List, Dict
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class FaissVectorStore:
    """
    A lightweight, in-memory Vector Store using FAISS and sentence-transformers.
    Designed to hold document chunks uploaded during a session for RAG queries.
    """
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        # Load the sentence transformer model (downloads it on first run, very small)
        self.encoder = SentenceTransformer(model_name)
        self.dimension = self.encoder.get_sentence_embedding_dimension()
        
        # Initialize an empty L2 (Euclidean distance) FAISS index
        self.index = faiss.IndexFlatL2(self.dimension)
        
        # Metadata storage (mapping index -> chunk dictionary)
        self.chunk_metadata: List[Dict[str, str]] = []
        
    def add_documents(self, chunks: List[Dict[str, str]]):
        """
        Embeds chunks of text and adds them to the FAISS index.
        Each chunk should be a dict: {"text": "...", "source": "...", "metadata": "..."}
        """
        if not chunks:
            return
            
        texts = [chunk["text"] for chunk in chunks]
        
        # Generate embeddings (N, dimension)
        embeddings = self.encoder.encode(texts, convert_to_numpy=True)
        
        # Add to FAISS
        self.index.add(embeddings)
        
        # Store metadata exactly in the order they were added
        self.chunk_metadata.extend(chunks)
        logger.info(f"Added {len(chunks)} document chunks to FAISS vector store. Total chunks: {self.index.ntotal}")

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, str]]:
        """
        Embeds the query, searches FAISS, and returns the top_k most similar chunks.
        """
        if self.index.ntotal == 0:
            return []
            
        # Ensure top_k doesn't exceed total documents
        k = min(top_k, self.index.ntotal)
        
        # Embed query
        query_embedding = self.encoder.encode([query], convert_to_numpy=True)
        
        # Search index
        distances, indices = self.index.search(query_embedding, k)
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx != -1:
                chunk = self.chunk_metadata[idx].copy()
                chunk["score"] = float(distances[0][i])
                results.append(chunk)
                
        return results

# Singleton instance to hold all uploaded documents in memory for the active backend instance
# Note: In production with multiple workers, this should be backed by Redis or an external VectorDB
global_vector_store = FaissVectorStore()
