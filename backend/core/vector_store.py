import logging
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
from core.mongodb import mongodb_connection
import numpy as np

logger = logging.getLogger(__name__)

class MongoDBVectorStore:
    """
    A Vector Store using MongoDB to persist chunks and their embeddings.
    Uses sentence-transformers to generate embeddings.
    """
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        # Load the sentence transformer model (downloads it on first run, very small)
        self.encoder = SentenceTransformer(model_name)
        self.dimension = self.encoder.get_sentence_embedding_dimension()
        
    async def add_documents(self, project_id: str, cloudinary_url: str, chunks: List[Dict[str, str]]):
        """
        Embeds chunks of text and adds them to MongoDB 'knowledge' collection.
        Each chunk should be a dict: {"text": "...", "source": "...", "metadata": "..."}
        """
        if not chunks:
            return
            
        texts = [chunk["text"] for chunk in chunks]
        
        # Generate embeddings (N, dimension)
        embeddings = self.encoder.encode(texts, convert_to_numpy=True)
        
        db = mongodb_connection.db
        
        documents = []
        for i, chunk in enumerate(chunks):
            doc = {
                "project_id": project_id,
                "cloudinary_url": cloudinary_url,
                "text": chunk["text"],
                "source": chunk.get("source", ""),
                "metadata": chunk.get("metadata", ""),
                "embedding": embeddings[i].tolist()
            }
            documents.append(doc)
            
        await db.knowledge.insert_many(documents)
        logger.info(f"Added {len(chunks)} document chunks to MongoDB knowledge collection for project {project_id}.")

    async def search(self, project_id: str, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Embeds the query, and performs a manual cosine similarity search across the project's chunks.
        Note: For large scale, use MongoDB Atlas Vector Search ($vectorSearch).
        """
        db = mongodb_connection.db
        
        # Embed query
        query_embedding = self.encoder.encode([query], convert_to_numpy=True)[0]
        
        # Fetch all chunks for the project
        cursor = db.knowledge.find({"project_id": project_id})
        chunks = await cursor.to_list(length=None)
        
        if not chunks:
            return []
            
        # Calculate cosine similarity manually in memory (since we don't have guaranteed Atlas Vector Search setup)
        def cosine_similarity(a, b):
            return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
            
        for chunk in chunks:
            chunk_embedding = np.array(chunk["embedding"])
            chunk["score"] = float(cosine_similarity(query_embedding, chunk_embedding))
            # Remove embedding from output to save bandwidth
            del chunk["embedding"]
            del chunk["_id"]
            
        # Sort by score descending
        chunks.sort(key=lambda x: x["score"], reverse=True)
        
        return chunks[:top_k]

global_vector_store = MongoDBVectorStore()

