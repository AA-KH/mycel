import json
import logging

logger = logging.getLogger(__name__)

VIKRAM_SPECIFIC_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "plan_emergency_rerouting",
            "description": "Calculates the time and cost premium of rerouting shipments around a blocked node (e.g., avoiding Suez Canal via Cape of Good Hope).",
            "parameters": {
                "type": "object",
                "properties": {
                    "origin": {
                        "type": "string",
                        "description": "Origin port or city."
                    },
                    "destination": {
                        "type": "string",
                        "description": "Destination port or city."
                    },
                    "blocked_node": {
                        "type": "string",
                        "description": "The node to avoid (e.g., 'Suez Canal', 'Port of LA')."
                    }
                },
                "required": ["origin", "destination", "blocked_node"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "evaluate_backup_capacity",
            "description": "Checks if a backup supplier has the physical capacity to handle an emergency production order.",
            "parameters": {
                "type": "object",
                "properties": {
                    "supplier_name": {
                        "type": "string",
                        "description": "Name of the backup supplier."
                    },
                    "required_units": {
                        "type": "integer",
                        "description": "The number of units needed in the emergency order."
                    }
                },
                "required": ["supplier_name", "required_units"]
            }
        }
    }
]

async def plan_emergency_rerouting(origin: str, destination: str, blocked_node: str) -> str:
    """Calculates alternate routing paths."""
    try:
        # Mock logic for rerouting
        if "suez" in blocked_node.lower():
            alternate_route = "Cape of Good Hope"
            added_transit_time_days = 14
            added_fuel_cost_usd = 450000
            insight = f"Rerouting via {alternate_route} adds {added_transit_time_days} days and ${added_fuel_cost_usd:,.2f} in fuel costs."
        elif "taiwan" in blocked_node.lower() or "tw" == blocked_node.lower():
            alternate_route = "Air Freight from Vietnam or US"
            added_transit_time_days = -5 # Air is faster
            added_fuel_cost_usd = 1200000 # But way more expensive
            insight = f"Switching to {alternate_route} saves time but incurs a massive premium of ${added_fuel_cost_usd:,.2f}."
        else:
            alternate_route = "Standard Alternate Highway/Port"
            added_transit_time_days = 3
            added_fuel_cost_usd = 50000
            insight = f"Minor rerouting adds {added_transit_time_days} days and ${added_fuel_cost_usd:,.2f}."

        return json.dumps({
            "original_origin": origin,
            "original_destination": destination,
            "blocked_node": blocked_node,
            "alternate_route": alternate_route,
            "added_transit_time_days": added_transit_time_days,
            "added_cost_usd": added_fuel_cost_usd,
            "insight": insight
        }, indent=2)
    except Exception as e:
        return f"Error planning emergency reroute: {str(e)}"

async def evaluate_backup_capacity(supplier_name: str, required_units: int) -> str:
    """Checks if a backup supplier can actually fulfill an emergency order."""
    try:
        name_lower = supplier_name.lower()
        
        # Simulated database logic
        if "tsmc" in name_lower:
            available_capacity = 0
            status = "NO CAPACITY"
        elif "globalfoundries" in name_lower:
            available_capacity = 50000
            status = "PARTIAL CAPACITY" if required_units > 50000 else "SUFFICIENT CAPACITY"
        elif "intel" in name_lower:
            available_capacity = 250000
            status = "SUFFICIENT CAPACITY"
        else:
            available_capacity = int(required_units * 0.8) # Arbitrary fallback
            status = "PARTIAL CAPACITY"

        can_fulfill = available_capacity >= required_units
        
        return json.dumps({
            "supplier": supplier_name,
            "requested_units": required_units,
            "available_capacity": available_capacity,
            "can_fulfill_completely": can_fulfill,
            "status": status,
            "insight": f"{supplier_name} can provide {available_capacity} units immediately."
        }, indent=2)
    except Exception as e:
        return f"Error evaluating capacity: {str(e)}"
