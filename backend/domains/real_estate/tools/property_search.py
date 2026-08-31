"""
Tool: property.search
Performs deterministic MongoDB-backed structured property search.
No LLM involved for filtering — purely numeric/categorical.
"""
from typing import Dict, Any
import logging

from tools.base import BaseTool
from tools.models import ToolDefinition
from agents.runtime.result import ToolResult
from tools.context import ToolExecutionContext
from domains.real_estate.ingestion import search_properties
import google.generativeai as genai
from core.config import settings
import math

def cosine_similarity(v1, v2):
    if not v1 or not v2: return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    mag1 = math.sqrt(sum(a * a for a in v1))
    mag2 = math.sqrt(sum(b * b for b in v2))
    if mag1 == 0 or mag2 == 0: return 0.0
    return dot / (mag1 * mag2)

logger = logging.getLogger(__name__)


class PropertySearchTool(BaseTool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            id="property.search",
            name="Property Search",
            category="real_estate",
            description=(
                "Searches for properties using structured filters: budget_max (numeric, INR), "
                "bhk (integer), location (string). Uses MongoDB for deterministic filtering. "
                "Do NOT use RAG for structured numeric filters."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "budget_max": {"type": "number", "description": "Maximum budget in INR"},
                    "bhk": {"type": "integer", "description": "Number of bedrooms"},
                    "location": {"type": "string", "description": "City or locality"},
                    "semantic_query": {"type": "string", "description": "A natural language query to find conceptually similar properties (e.g. 'peaceful with sea view')"},
                    "limit": {"type": "integer", "default": 10}
                }
            },
            capabilities=["property_search"],
            risk_level="low",
        )

    async def execute(self, arguments: Dict[str, Any], context: ToolExecutionContext) -> ToolResult:
        logger.info(f"[property.search] Filters: {arguments}")

        results = await search_properties(
            budget_max=arguments.get("budget_max"),
            bhk=arguments.get("bhk"),
            location=arguments.get("location"),
            limit=arguments.get("limit", 10),
        )

        semantic_query = arguments.get("semantic_query")
        query_embedding = None
        
        if semantic_query and settings.gemini_api_key:
            try:
                genai.configure(api_key=settings.gemini_api_key)
                response = genai.embed_content(
                    model="models/embedding-001",
                    content=semantic_query,
                    task_type="retrieval_query"
                )
                query_embedding = response["embedding"]
            except Exception as e:
                logger.warning(f"[property.search] Failed to generate query embedding: {e}")

        scored = []
        for r in results:
            score = 100.0
            req_fields = [k for k in ["budget_max", "bhk", "location"] if arguments.get(k) is not None]
            score = max(70.0, score - (len(req_fields) * 2))  # slight deduction per filter used
            
            # If semantic search was requested, re-score based on cosine similarity
            if query_embedding and r.get("embedding"):
                sim = cosine_similarity(query_embedding, r["embedding"])
                score = (score * 0.3) + (sim * 100 * 0.7)  # 70% weight to vector similarity
            
            r["match_score"] = round(score, 1)
            # Remove embedding from output to save tokens
            if "embedding" in r:
                del r["embedding"]
                
            scored.append(r)
            
        if query_embedding:
            # Sort by highest score first if using vector search
            scored = sorted(scored, key=lambda x: x["match_score"], reverse=True)

        logger.info(f"[property.search] Found {len(scored)} results.")
        return ToolResult(
            tool_name="property.search",
            status="success",
            output={"results": scored, "count": len(scored)},
        )
