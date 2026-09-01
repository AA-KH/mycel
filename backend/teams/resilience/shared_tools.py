import json
import logging

logger = logging.getLogger(__name__)

RESILIENCE_SHARED_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "calculate_financial_impact",
            "description": "Calculates the total financial loss of a supply chain disruption.",
            "parameters": {
                "type": "object",
                "properties": {
                    "downtime_days": {
                        "type": "integer",
                        "description": "Estimated number of days the supply chain node will be offline."
                    },
                    "daily_revenue_loss": {
                        "type": "number",
                        "description": "Lost sales revenue per day in USD."
                    },
                    "fixed_costs_per_day": {
                        "type": "number",
                        "description": "Fixed operational costs per day (e.g., idle labor, warehouse lease) in USD."
                    }
                },
                "required": ["downtime_days", "daily_revenue_loss", "fixed_costs_per_day"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_alternate_suppliers",
            "description": "Searches a simulated database for backup suppliers when a primary region is compromised.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_category": {
                        "type": "string",
                        "description": "The category of goods (e.g., 'Semiconductors', 'Textiles', 'Automotive Parts')."
                    },
                    "avoid_region": {
                        "type": "string",
                        "description": "The compromised region/country code to exclude from the search (e.g., 'TW', 'CN')."
                    }
                },
                "required": ["product_category", "avoid_region"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "estimate_emergency_freight",
            "description": "Estimates the massive premium cost of booking emergency air charters or expedited road freight.",
            "parameters": {
                "type": "object",
                "properties": {
                    "weight_kg": {
                        "type": "number",
                        "description": "Total weight of the emergency shipment in kg."
                    },
                    "mode": {
                        "type": "string",
                        "description": "Must be 'Air Charter' or 'Expedited Road'."
                    }
                },
                "required": ["weight_kg", "mode"]
            }
        }
    }
]

async def calculate_financial_impact(downtime_days: int, daily_revenue_loss: float, fixed_costs_per_day: float) -> str:
    try:
        total_lost_revenue = downtime_days * daily_revenue_loss
        total_wasted_fixed_costs = downtime_days * fixed_costs_per_day
        total_impact = total_lost_revenue + total_wasted_fixed_costs
        
        return json.dumps({
            "downtime_days": downtime_days,
            "total_lost_revenue_usd": total_lost_revenue,
            "total_wasted_fixed_costs_usd": total_wasted_fixed_costs,
            "total_financial_impact_usd": total_impact,
            "insight": f"A {downtime_days}-day disruption will cost the company ${total_impact:,.2f}. Any backup plan costing less than this is mathematically viable."
        }, indent=2)
    except Exception as e:
        return f"Error calculating impact: {str(e)}"

async def search_alternate_suppliers(product_category: str, avoid_region: str) -> str:
    try:
        # Simulated backup supplier database
        database = {
            "semiconductors": [
                {"name": "Intel Foundry Services", "region": "US", "lead_time_days": 45, "price_premium_percent": 30},
                {"name": "GlobalFoundries", "region": "DE", "lead_time_days": 60, "price_premium_percent": 25},
                {"name": "TSMC", "region": "TW", "lead_time_days": 14, "price_premium_percent": 0}
            ],
            "textiles": [
                {"name": "Vintex", "region": "VN", "lead_time_days": 30, "price_premium_percent": 5},
                {"name": "MexFabrics", "region": "MX", "lead_time_days": 15, "price_premium_percent": 12},
                {"name": "SinoWeave", "region": "CN", "lead_time_days": 20, "price_premium_percent": 0}
            ]
        }
        
        category = product_category.lower()
        if category not in database:
            return json.dumps({"error": f"No backup suppliers found for category: {product_category}"})
            
        all_suppliers = database[category]
        valid_suppliers = [s for s in all_suppliers if s["region"].upper() != avoid_region.upper()]
        
        if not valid_suppliers:
            return json.dumps({"status": "CRITICAL", "message": f"No alternate suppliers exist outside of {avoid_region}!"})
            
        return json.dumps({
            "status": "Found",
            "avoided_region": avoid_region,
            "alternate_suppliers": valid_suppliers
        }, indent=2)
    except Exception as e:
        return f"Error searching suppliers: {str(e)}"

async def estimate_emergency_freight(weight_kg: float, mode: str) -> str:
    try:
        if mode.lower() == "air charter":
            # Very expensive: $15 per kg + $50k base charter fee
            cost = (weight_kg * 15.0) + 50000.0
            time = "1-3 Days"
        elif mode.lower() == "expedited road":
            # $3 per kg + $5k base team-driver fee
            cost = (weight_kg * 3.0) + 5000.0
            time = "3-5 Days"
        else:
            return "Error: Mode must be 'Air Charter' or 'Expedited Road'"
            
        return json.dumps({
            "mode": mode,
            "weight_kg": weight_kg,
            "estimated_transit_time": time,
            "total_emergency_cost_usd": cost,
            "insight": f"{mode} will cost ${cost:,.2f} for {weight_kg}kg."
        }, indent=2)
    except Exception as e:
        return f"Error estimating freight: {str(e)}"
