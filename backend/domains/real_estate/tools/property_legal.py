"""
Tool: property.legal_knowledge
Retrieves synthetic legal reference material for property regulations.
This is a RAG-style retrieval — deterministic lookups against seeded knowledge.

All responses include:
- source_type: always "LEGAL_KNOWLEDGE_BASE"
- source_document: the seeded document identifier
- confidence: confidence in the match
- disclaimer: always present for legal safety
"""
from typing import Dict, Any
import logging

from tools.base import BaseTool
from tools.models import ToolDefinition
from agents.runtime.result import ToolResult
from tools.context import ToolExecutionContext

logger = logging.getLogger(__name__)

# Synthetic legal knowledge base — seeded for demo
# In production this would be a Qdrant vector index
LEGAL_KNOWLEDGE_BASE = [
    {
        "doc_id": "LKB-001",
        "title": "Residential Setback Requirements — Punjab Municipal Building Bylaws",
        "keywords": ["setback", "gaj", "aage", "plot", "front", "boundary", "leave", "vacant"],
        "content": (
            "As per Punjab Municipal Building Bylaws (2022), residential plots must maintain the following setback distances: "
            "Plots up to 100 sq yd: Front setback = 10 ft (approx 3.05m). "
            "Plots 101-200 sq yd: Front setback = 12.5 ft. "
            "Plots above 200 sq yd: Front setback = 15 ft. "
            "Side setbacks: minimum 3 ft. Rear setback: minimum 6 ft. "
            "A '50 gaj ki jagah aage chhodna' (leaving 50 sq yd in front) is NOT a standard bylaw requirement — "
            "standard requirements specify linear setback distances in feet, not area in square yards. "
            "Verify exact requirements with the local municipal corporation for your specific plot."
        ),
        "confidence": 0.87,
    },
    {
        "doc_id": "LKB-002",
        "title": "RERA Punjab — Property Registration and Disclosure Requirements",
        "keywords": ["rera", "registration", "disclosure", "buyer", "developer", "complaint"],
        "content": (
            "Under RERA Punjab (Real Estate Regulatory Authority), developers must register all residential projects "
            "with more than 8 units before marketing or selling. Buyers have the right to: "
            "1. Receive a copy of the approved building plan. "
            "2. Obtain possession within the timeline specified in the sale agreement. "
            "3. File a complaint with HRERA (Haryana RERA) or RERA Punjab. "
            "Penalty: Developers can be fined up to 5% of project cost for non-disclosure."
        ),
        "confidence": 0.92,
    },
    {
        "doc_id": "LKB-003",
        "title": "Stamp Duty and Registration Charges — Punjab/Haryana",
        "keywords": ["stamp duty", "registration", "charge", "fee", "transfer", "deed"],
        "content": (
            "Stamp Duty in Punjab: 5% for male buyers, 3% for female buyers (on circle rate or agreement value, whichever is higher). "
            "Registration Charges: 1% of property value (max ₹50,000). "
            "In Haryana: Stamp Duty = 7% (male), 5% (female). "
            "GST applies on under-construction properties at 5% (without ITC) or 12% (with ITC). "
            "Ready-to-move properties are exempt from GST if OC (Occupancy Certificate) is obtained."
        ),
        "confidence": 0.89,
    },
    {
        "doc_id": "LKB-004",
        "title": "Floor Area Ratio (FAR) and Coverage Rules",
        "keywords": ["far", "floor area ratio", "coverage", "construction", "floors", "height"],
        "content": (
            "Floor Area Ratio (FAR) in Chandigarh/Tricity region: "
            "Chandigarh sectors (residential): FAR = 1.33 to 1.75 depending on sector classification. "
            "Mohali/SAS Nagar: FAR = 1.75 (up to 4 floors typically permitted for residential). "
            "Coverage: Maximum ground coverage is 50-65% of the plot area depending on plot size. "
            "Heights are restricted in Chandigarh at 15m (approximately 5 floors) for most residential zones."
        ),
        "confidence": 0.84,
    },
]


import numpy as np
import google.generativeai as genai
from core.config import settings

def cosine_similarity(vec1, vec2):
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot_product / (norm1 * norm2)

def _retrieve_legal_knowledge(query: str) -> Dict[str, Any]:
    """Retrieve best chunk from _KNOWLEDGE_CHUNKS using fast cosine similarity."""
    from domains.real_estate.ingestion import _KNOWLEDGE_CHUNKS
    
    # 1. Check if we have chunks in memory
    if not _KNOWLEDGE_CHUNKS:
        # Fallback to static keyword search if no docs uploaded
        query_lower = query.lower()
        best_match = None
        best_score = 0.0
        for doc in LEGAL_KNOWLEDGE_BASE:
            keyword_hits = sum(1 for kw in doc["keywords"] if kw in query_lower)
            if keyword_hits > best_score:
                best_score = keyword_hits
                best_match = doc
        if best_match and best_score > 0:
            return best_match
        return {
            "doc_id": "LKB-GENERAL",
            "title": "General Property Legal Guidance",
            "content": (
                "Property laws vary by state and municipal authority. "
                "Key areas include: setback requirements, FAR/coverage limits, stamp duty, RERA compliance. "
                "Always verify with the local municipal corporation or a qualified property lawyer."
            ),
            "confidence": 0.60,
        }
        
    # 2. Compute query embedding
    try:
        if settings.gemini_api_key:
            genai.configure(api_key=settings.gemini_api_key)
            response = genai.embed_content(
                model="models/gemini-embedding-2",
                content=query,
                task_type="retrieval_query"
            )
            query_embedding = np.array(response["embedding"])
        else:
            raise ValueError("Gemini API key not configured")
    except Exception as e:
        logger.error(f"Failed to embed query: {e}")
        return LEGAL_KNOWLEDGE_BASE[0] # Fallback
        
    # 3. Find top match using numpy cosine similarity
    best_chunk = None
    best_score = -1.0
    
    for chunk in _KNOWLEDGE_CHUNKS:
        chunk_embedding = np.array(chunk["embedding"])
        score = cosine_similarity(query_embedding, chunk_embedding)
        if score > best_score:
            best_score = score
            best_chunk = chunk
            
    if best_chunk and best_score > 0.6: # Threshold
        return {
            "doc_id": best_chunk["doc_id"],
            "title": best_chunk["title"],
            "content": best_chunk["content"],
            "confidence": best_score,
        }
    else:
        return {
            "doc_id": "LKB-GENERAL",
            "title": "General Property Legal Guidance",
            "content": "I couldn't find a highly relevant match in our uploaded knowledge base. Please ask an expert.",
            "confidence": best_score if best_chunk else 0.0,
        }


class PropertyLegalTool(BaseTool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            id="property.legal_knowledge",
            name="Property Legal Knowledge",
            category="real_estate",
            description=(
                "Retrieves approved legal reference material for property regulations, setbacks, "
                "RERA, stamp duty, FAR, and related legal topics. "
                "Always includes source attribution and disclaimer. "
                "Never invents laws — only returns seeded knowledge base content."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The legal question in any language"
                    }
                },
                "required": ["query"]
            },
            capabilities=["property_legal_knowledge"],
            risk_level="low",
        )

    async def execute(self, arguments: Dict[str, Any], context: ToolExecutionContext) -> ToolResult:
        query = arguments.get("query", "")
        logger.info(f"[property.legal_knowledge] Query: {query[:100]}")

        doc = _retrieve_legal_knowledge(query)

        return ToolResult(
            tool_name="property.legal_knowledge",
            status="success",
            output={
                "source_type": "LEGAL_KNOWLEDGE_BASE",
                "source_document": doc["doc_id"],
                "document_title": doc.get("title", ""),
                "content": doc["content"],
                "confidence": doc.get("confidence", 0.75),
                "retrieval_status": "completed",
                "disclaimer": (
                    "This information is from a synthetic legal reference database for demonstration purposes. "
                    "Always verify property legal requirements with qualified professionals and local authorities."
                ),
            },
        )
