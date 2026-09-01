import logging
import json
import math

logger = logging.getLogger(__name__)

# --- SCHEMAS ---
TARA_SPECIFIC_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "calculate_storage_utilization",
            "description": "Calculates the physical space utilization of the warehouse. A utilization above 85% usually indicates a capacity constraint.",
            "parameters": {
                "type": "object",
                "properties": {
                    "total_pallet_positions": {
                        "type": "integer",
                        "description": "Total physical storage slots available in the warehouse."
                    },
                    "current_inventory_pallets": {
                        "type": "integer",
                        "description": "Current number of pallets occupying space."
                    },
                    "incoming_pallets": {
                        "type": "integer",
                        "description": "Number of new pallets expected to arrive."
                    }
                },
                "required": ["total_pallet_positions", "current_inventory_pallets", "incoming_pallets"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "schedule_dock_appointments",
            "description": "Analyzes inbound truck volume against dock door availability to determine required shifts and identify queuing delays.",
            "parameters": {
                "type": "object",
                "properties": {
                    "inbound_trucks": {
                        "type": "integer",
                        "description": "Number of trucks arriving."
                    },
                    "dock_doors": {
                        "type": "integer",
                        "description": "Number of available dock doors for unloading."
                    },
                    "unload_time_hours": {
                        "type": "number",
                        "description": "Average time required to unload one truck (in hours)."
                    },
                    "working_hours": {
                        "type": "number",
                        "description": "Length of the standard processing window (e.g., 9 for an 8 AM - 5 PM shift)."
                    }
                },
                "required": ["inbound_trucks", "dock_doors", "unload_time_hours", "working_hours"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_throughput_bottleneck",
            "description": "Analyzes the operational flow rates across the four primary warehouse stages to identify the exact bottleneck.",
            "parameters": {
                "type": "object",
                "properties": {
                    "inbound_rate": {
                        "type": "number",
                        "description": "Pallets unloaded per hour."
                    },
                    "putaway_rate": {
                        "type": "number",
                        "description": "Pallets moved from dock to storage per hour."
                    },
                    "picking_rate": {
                        "type": "number",
                        "description": "Pallets (or equivalent volume) picked from storage per hour."
                    },
                    "outbound_rate": {
                        "type": "number",
                        "description": "Pallets loaded onto outbound trucks per hour."
                    }
                },
                "required": ["inbound_rate", "putaway_rate", "picking_rate", "outbound_rate"]
            }
        }
    }
]

# --- IMPLEMENTATIONS ---

async def calculate_storage_utilization(total_pallet_positions: int, current_inventory_pallets: int, incoming_pallets: int) -> str:
    """Calculates warehouse storage utilization and flags capacity constraints."""
    try:
        if total_pallet_positions <= 0:
            return "Error: total_pallet_positions must be greater than zero."
            
        future_pallets = current_inventory_pallets + incoming_pallets
        utilization_percent = (future_pallets / total_pallet_positions) * 100
        
        status = "Healthy"
        if utilization_percent >= 100:
            status = "CRITICAL: OVER CAPACITY"
        elif utilization_percent >= 85:
            status = "WARNING: CONGESTION RISK (Standard max threshold is 85%)"
            
        result = {
            "total_positions": total_pallet_positions,
            "future_occupied_positions": future_pallets,
            "utilization_percent": round(utilization_percent, 2),
            "status": status,
            "free_positions_remaining": max(0, total_pallet_positions - future_pallets)
        }
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error calculating storage utilization: {str(e)}"

async def schedule_dock_appointments(inbound_trucks: int, dock_doors: int, unload_time_hours: float, working_hours: float) -> str:
    """Analyzes dock scheduling capacity."""
    try:
        if dock_doors <= 0 or unload_time_hours <= 0:
            return "Error: dock_doors and unload_time_hours must be greater than zero."
            
        # Maximum trucks one door can process in the working window
        trucks_per_door = math.floor(working_hours / unload_time_hours)
        total_capacity = trucks_per_door * dock_doors
        
        # Calculate time required to process all trucks
        batches_required = math.ceil(inbound_trucks / dock_doors)
        total_time_required = batches_required * unload_time_hours
        
        queue_expected = inbound_trucks > total_capacity
        
        result = {
            "total_capacity_trucks": total_capacity,
            "trucks_to_process": inbound_trucks,
            "total_hours_required": total_time_required,
            "can_complete_in_window": total_time_required <= working_hours,
            "queue_expected": queue_expected,
            "recommendation": "Add a shift or overtime" if queue_expected else "Standard schedule is sufficient"
        }
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error scheduling dock appointments: {str(e)}"

async def calculate_throughput_bottleneck(inbound_rate: float, putaway_rate: float, picking_rate: float, outbound_rate: float) -> str:
    """Finds the lowest throughput stage (the bottleneck)."""
    try:
        rates = {
            "Inbound": inbound_rate,
            "Putaway": putaway_rate,
            "Picking": picking_rate,
            "Outbound": outbound_rate
        }
        
        bottleneck_stage = min(rates, key=rates.get)
        bottleneck_rate = rates[bottleneck_stage]
        
        system_throughput = bottleneck_rate
        
        result = {
            "rates_pallets_per_hour": rates,
            "critical_bottleneck_stage": bottleneck_stage,
            "max_system_throughput": system_throughput,
            "insight": f"The entire warehouse can only process {system_throughput} pallets/hour due to constraints at the {bottleneck_stage} stage."
        }
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error calculating bottleneck: {str(e)}"
