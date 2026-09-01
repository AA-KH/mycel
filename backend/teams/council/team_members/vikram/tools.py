import json

VIKRAM_SPECIFIC_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "score_supply_chain_resilience",
            "description": "Scores the overall resilience of a supply chain setup (0=fragile, 100=highly resilient). Evaluates supplier count, geographic spread, inventory buffers, and lead time variance.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_category": {"type": "string"},
                    "num_active_suppliers": {"type": "integer", "description": "Number of active, qualified suppliers for this category."},
                    "num_countries_sourced_from": {"type": "integer", "description": "Number of distinct countries in the supplier base."},
                    "avg_lead_time_days": {"type": "number", "description": "Average lead time from order to delivery in days."},
                    "safety_stock_days": {"type": "number", "description": "Days of safety stock held."},
                    "single_source_pct": {"type": "number", "description": "Percentage of volume sourced from a single supplier (0-100)."}
                },
                "required": ["product_category", "num_active_suppliers", "num_countries_sourced_from", "avg_lead_time_days", "safety_stock_days", "single_source_pct"]
            }
        }
    }
]

async def score_supply_chain_resilience(
    product_category: str,
    num_active_suppliers: int,
    num_countries_sourced_from: int,
    avg_lead_time_days: float,
    safety_stock_days: float,
    single_source_pct: float
) -> str:
    try:
        score = 0
        factors = []

        # Supplier diversity
        if num_active_suppliers >= 5:
            score += 25; factors.append("5+ active suppliers: +25 (Excellent diversity)")
        elif num_active_suppliers >= 3:
            score += 15; factors.append("3-4 active suppliers: +15 (Good)")
        elif num_active_suppliers == 2:
            score += 7; factors.append("2 suppliers: +7 (Minimal backup)")
        else:
            factors.append("Only 1 supplier: +0 (CRITICAL single-source risk)")

        # Geographic spread
        if num_countries_sourced_from >= 4:
            score += 25; factors.append(f"{num_countries_sourced_from} countries: +25 (Excellent geo-spread)")
        elif num_countries_sourced_from >= 2:
            score += 15; factors.append(f"{num_countries_sourced_from} countries: +15 (Moderate)")
        else:
            factors.append("Single-country sourcing: +0 (Geopolitical concentration risk)")

        # Lead time
        if avg_lead_time_days <= 14:
            score += 20; factors.append(f"Lead time {avg_lead_time_days}d: +20 (Agile)")
        elif avg_lead_time_days <= 30:
            score += 12; factors.append(f"Lead time {avg_lead_time_days}d: +12 (Acceptable)")
        elif avg_lead_time_days <= 60:
            score += 5; factors.append(f"Lead time {avg_lead_time_days}d: +5 (Long — monitor closely)")
        else:
            factors.append(f"Lead time {avg_lead_time_days}d: +0 (CRITICAL — over 60 days)")

        # Safety stock
        if safety_stock_days >= 45:
            score += 20; factors.append(f"{safety_stock_days}d safety stock: +20 (Strong buffer)")
        elif safety_stock_days >= 21:
            score += 12; factors.append(f"{safety_stock_days}d safety stock: +12 (Adequate)")
        elif safety_stock_days >= 7:
            score += 5; factors.append(f"{safety_stock_days}d safety stock: +5 (Thin buffer)")
        else:
            factors.append(f"{safety_stock_days}d safety stock: +0 (CRITICAL — near zero buffer)")

        # Single source penalty
        if single_source_pct <= 20:
            score += 10; factors.append(f"Single-source %: {single_source_pct}% — +10 (Well-diversified)")
        elif single_source_pct <= 50:
            score += 5; factors.append(f"Single-source %: {single_source_pct}% — +5 (Concentration building)")
        else:
            factors.append(f"Single-source %: {single_source_pct}% — +0 (DANGEROUS concentration)")

        score = min(score, 100)

        if score >= 75:
            verdict = "RESILIENT — Approve with standard review cycle"
        elif score >= 50:
            verdict = "MODERATE — Require dual-source contingency plan before Council approval"
        else:
            verdict = "FRAGILE — BLOCK approval. Mandate supplier diversification program immediately."

        return json.dumps({
            "product_category": product_category,
            "resilience_score": score,
            "verdict": verdict,
            "scoring_breakdown": factors,
            "vikram_recommendation": verdict
        }, indent=2)
    except Exception as e:
        return f"Error scoring resilience: {str(e)}"
