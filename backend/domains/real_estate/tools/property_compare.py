"""
Tool: property.compare
Server-side comparison of multiple properties — no LLM for data fetching.
"""
from typing import Dict, Any
import logging

from tools.base import BaseTool
from tools.models import ToolDefinition
from agents.runtime.result import ToolResult
from tools.context import ToolExecutionContext
from domains.real_estate.ingestion import compare_properties

logger = logging.getLogger(__name__)

COMPARISON_FIELDS = [
    "property_id", "title", "price", "bhk", "area_sqft",
    "location", "city", "floor", "total_floors", "parking",
    "amenities", "developer", "availability", "rental_yield",
    "demand_score", "description"
]


class PropertyCompareTool(BaseTool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            id="property.compare",
            name="Property Comparison",
            category="real_estate",
            description=(
                "Compares multiple properties side-by-side on key attributes. "
                "Returns structured comparison table. No LLM for data fetching."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "property_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of property_id values to compare"
                    }
                },
                "required": ["property_ids"]
            },
            capabilities=["property_comparison"],
            risk_level="low",
        )

    async def execute(self, arguments: Dict[str, Any], context: ToolExecutionContext) -> ToolResult:
        property_ids = arguments.get("property_ids", [])
        if not property_ids:
            return ToolResult(
                tool_name="property.compare",
                status="error",
                output={},
                error="No property_ids provided"
            )

        logger.info(f"[property.compare] Comparing {len(property_ids)} properties")

        records = await compare_properties(property_ids)

        # Build comparison matrix
        comparison = []
        for field in COMPARISON_FIELDS:
            row = {"field": field}
            for rec in records:
                pid = rec.get("property_id", "unknown")
                row[pid] = rec.get(field, "N/A")
            comparison.append(row)

        return ToolResult(
            tool_name="property.compare",
            status="success",
            output={
                "properties": records,
                "comparison_matrix": comparison,
                "count": len(records)
            },
        )
