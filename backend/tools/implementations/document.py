from typing import Dict, Any, List
import logging
from core.vector_store import global_vector_store

logger = logging.getLogger(__name__)

def search_internal_documents(query: str, top_k: int = 3) -> str:
    """
    Search the internal knowledge base (uploaded documents) for specific information.
    Use this when you need facts, figures, or details from the user's uploaded files (e.g. inventory, suppliers, BOM).
    """
    try:
        results = global_vector_store.search(query=query, top_k=top_k)
        
        if not results:
            return "No relevant information found in the internal documents. The user might not have uploaded relevant files yet."
            
        formatted_results = []
        for i, res in enumerate(results):
            source = res.get("source", "Unknown file")
            meta = res.get("metadata", "")
            text = res.get("text", "").strip()
            
            formatted_results.append(f"--- Document {i+1} [Source: {source} | {meta}] ---\n{text}\n")
            
        return "\n".join(formatted_results)
        
    except Exception as e:
        logger.error(f"Failed to search internal documents: {e}")
        return f"Error searching documents: {str(e)}"

# Define the tool schema for the LLM
SEARCH_DOCUMENTS_TOOL = {
    "type": "function",
    "function": {
        "name": "search_internal_documents",
        "description": "Search the user's uploaded internal documents (CSV, Excel, PDF) to find specific facts, rows, or paragraphs.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The specific question or keywords to search for (e.g. 'Who is the top supplier for rare earth metals?' or 'What is the inventory for Part A?')"
                },
                "top_k": {
                    "type": "integer",
                    "description": "Number of results to return (max 5)",
                    "default": 3
                }
            },
            "required": ["query"]
        }
    }
}
