"""
Tool: property.investment_analysis
Deterministic rental yield, ROI, and investment ranking.
No LLM used for calculations — pure arithmetic.
LLM used only for natural-language explanation if needed (optional).
"""
from typing import Dict, Any, List
import logging

from tools.base import BaseTool
from tools.models import ToolDefinition
from agents.runtime.result import ToolResult
from tools.context import ToolExecutionContext
from domains.real_estate.ingestion import compare_properties

logger = logging.getLogger(__name__)


def _calculate_investment_metrics(prop: Dict) -> Dict:
    """Pure arithmetic — no LLM."""
    price = prop.get("price") or 0
    rental_yield_pct = prop.get("rental_yield") or 0
    
    annual_rental = (price * rental_yield_pct / 100) if price and rental_yield_pct else None
    monthly_rental = (annual_rental / 12) if annual_rental else None
    
    # Simple ROI estimate: rental yield + historical appreciation proxy
    historical = prop.get("historical_price")
    price_appreciation_pct = None
    if historical and price and historical > 0:
        price_appreciation_pct = round(((price - historical) / historical) * 100, 2)
    
    demand_score = prop.get("demand_score") or 50.0
    
    # Composite investment score (0-100)
    inv_score = 0.0
    if rental_yield_pct:
        inv_score += min(rental_yield_pct * 10, 50)   # max 50 pts from yield
    if price_appreciation_pct and price_appreciation_pct > 0:
        inv_score += min(price_appreciation_pct / 2, 30)  # max 30 pts from appreciation
    inv_score += demand_score * 0.20    # max 20 pts from demand

    return {
        "property_id": prop.get("property_id"),
        "title": prop.get("title"),
        "price": price,
        "rental_yield_pct": rental_yield_pct,
        "annual_rental_income": round(annual_rental, 2) if annual_rental else None,
        "monthly_rental_income": round(monthly_rental, 2) if monthly_rental else None,
        "price_appreciation_pct": price_appreciation_pct,
        "demand_score": demand_score,
        "investment_score": round(inv_score, 2),
    }


class PropertyInvestmentTool(BaseTool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            id="property.investment_analysis",
            name="Property Investment Analysis",
            category="real_estate",
            description=(
                "Performs deterministic rental yield, ROI, and investment ranking analysis "
                "for one or more properties. No LLM for calculations. "
                "Ranks by composite investment_score."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "property_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of property_id values to analyze"
                    }
                },
                "required": ["property_ids"]
            },
            capabilities=["investment_analysis", "rental_yield_analysis"],
            risk_level="low",
        )

    async def execute(self, arguments: Dict[str, Any], context: ToolExecutionContext) -> ToolResult:
        property_ids = arguments.get("property_ids", [])

        if not property_ids:
            return ToolResult(
                tool_name="property.investment_analysis",
                status="error",
                output={},
                error="No property_ids provided"
            )

        logger.info(f"[property.investment_analysis] Analyzing {len(property_ids)} properties")
        records = await compare_properties(property_ids)

        metrics = [_calculate_investment_metrics(r) for r in records]
        metrics.sort(key=lambda x: x.get("investment_score", 0), reverse=True)

        return ToolResult(
            tool_name="property.investment_analysis",
            status="success",
            output={
                "analysis": metrics,
                "top_pick": metrics[0] if metrics else None,
                "ranked_count": len(metrics),
                "source": "PROPERTY_DATABASE",
                "methodology": "Composite score: rental_yield (50%) + price_appreciation (30%) + demand_score (20%)"
            },
        )
