import logging
import json
import math

logger = logging.getLogger(__name__)

# --- SCHEMAS ---
KABIR_SPECIFIC_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "calculate_eoq",
            "description": "Calculates the Economic Order Quantity (EOQ), which is the optimal order size that minimizes total inventory costs (ordering + holding costs).",
            "parameters": {
                "type": "object",
                "properties": {
                    "annual_demand": {
                        "type": "integer",
                        "description": "Total expected demand for the year."
                    },
                    "order_cost": {
                        "type": "number",
                        "description": "Fixed cost per order placed (e.g., shipping, admin fees)."
                    },
                    "holding_cost_per_unit": {
                        "type": "number",
                        "description": "Cost to hold one unit in inventory for a year."
                    }
                },
                "required": ["annual_demand", "order_cost", "holding_cost_per_unit"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_safety_stock",
            "description": "Calculates statistical safety stock to prevent stockouts based on demand variability and desired service level.",
            "parameters": {
                "type": "object",
                "properties": {
                    "service_level_percent": {
                        "type": "number",
                        "description": "Desired service level percentage (e.g., 90, 95, 99). Higher percentage means more safety stock."
                    },
                    "std_dev_demand": {
                        "type": "number",
                        "description": "Standard deviation of daily demand."
                    },
                    "lead_time_days": {
                        "type": "number",
                        "description": "Supplier lead time in days."
                    }
                },
                "required": ["service_level_percent", "std_dev_demand", "lead_time_days"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "estimate_fulfillment_capacity",
            "description": "Calculates the total daily outbound fulfillment capacity of a warehouse based on labor and picking speed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pickers_count": {
                        "type": "integer",
                        "description": "Number of active warehouse pickers/packers."
                    },
                    "items_per_picker_per_hour": {
                        "type": "number",
                        "description": "Average number of items one picker can pick and pack in an hour."
                    },
                    "shift_hours": {
                        "type": "number",
                        "description": "Number of working hours per shift (excluding breaks, e.g., 7.5)."
                    },
                    "number_of_shifts": {
                        "type": "integer",
                        "description": "Number of shifts running per day (e.g., 1, 2, or 3)."
                    }
                },
                "required": ["pickers_count", "items_per_picker_per_hour", "shift_hours", "number_of_shifts"]
            }
        }
    }
]

# --- IMPLEMENTATIONS ---

async def calculate_eoq(annual_demand: int, order_cost: float, holding_cost_per_unit: float) -> str:
    """
    Calculates the Economic Order Quantity (EOQ).
    Formula: sqrt((2 * D * S) / H)
    """
    try:
        if holding_cost_per_unit <= 0:
            return "Error: Holding cost must be greater than zero."
            
        eoq = math.sqrt((2 * annual_demand * order_cost) / holding_cost_per_unit)
        optimal_order_qty = round(eoq)
        
        # Additional metrics
        orders_per_year = annual_demand / optimal_order_qty if optimal_order_qty > 0 else 0
        annual_ordering_cost = orders_per_year * order_cost
        annual_holding_cost = (optimal_order_qty / 2) * holding_cost_per_unit
        total_inventory_cost = annual_ordering_cost + annual_holding_cost
        
        result = {
            "economic_order_quantity": optimal_order_qty,
            "orders_per_year": round(orders_per_year, 1),
            "annual_ordering_cost": round(annual_ordering_cost, 2),
            "annual_holding_cost": round(annual_holding_cost, 2),
            "total_inventory_cost": round(total_inventory_cost, 2)
        }
        
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error calculating EOQ: {str(e)}"

async def calculate_safety_stock(service_level_percent: float, std_dev_demand: float, lead_time_days: float) -> str:
    """
    Calculates statistical safety stock.
    Formula: Z * std_dev_demand * sqrt(lead_time_days)
    """
    try:
        # Map common service levels to approximate Z-scores
        z_score_map = {
            80.0: 0.84,
            85.0: 1.04,
            90.0: 1.28,
            95.0: 1.65,
            97.7: 2.00,
            99.0: 2.33,
            99.9: 3.09
        }
        
        # Find closest service level in map
        closest_sl = min(z_score_map.keys(), key=lambda k: abs(k - service_level_percent))
        z_score = z_score_map[closest_sl]
        
        safety_stock_exact = z_score * std_dev_demand * math.sqrt(lead_time_days)
        safety_stock_rounded = math.ceil(safety_stock_exact)
        
        result = {
            "requested_service_level": service_level_percent,
            "mapped_service_level": closest_sl,
            "z_score_used": z_score,
            "safety_stock_units": safety_stock_rounded
        }
        
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error calculating safety stock: {str(e)}"

async def estimate_fulfillment_capacity(pickers_count: int, items_per_picker_per_hour: float, shift_hours: float, number_of_shifts: int) -> str:
    """
    Calculates total warehouse outbound capacity.
    """
    try:
        daily_capacity_per_picker = items_per_picker_per_hour * shift_hours
        total_daily_capacity = daily_capacity_per_picker * pickers_count * number_of_shifts
        weekly_capacity = total_daily_capacity * 7
        
        result = {
            "daily_capacity_units": int(total_daily_capacity),
            "weekly_capacity_units": int(weekly_capacity),
            "bottleneck_warning": "This assumes 100% utilization and no bottlenecks in packing/shipping docks."
        }
        
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error calculating fulfillment capacity: {str(e)}"
