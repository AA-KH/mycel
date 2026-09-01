import json

LEENA_SPECIFIC_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "run_capacity_stress_test",
            "description": "Applies a massive volume surge to the network to identify which specific node overflows (breaks) first.",
            "parameters": {
                "type": "object",
                "properties": {
                    "network_capacity": {
                        "type": "array",
                        "description": "List of nodes with their baseline capacity and current volume.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "node_name": {"type": "string"},
                                "max_capacity": {"type": "number"},
                                "current_volume": {"type": "number"}
                            },
                            "required": ["node_name", "max_capacity", "current_volume"]
                        }
                    },
                    "surge_multiplier": {
                        "type": "number",
                        "description": "The multiplier of the stress test (e.g., 2.0 for 200% surge)."
                    }
                },
                "required": ["network_capacity", "surge_multiplier"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "simulate_lead_time_shock",
            "description": "Calculates the exact stockout date if suppliers freeze operations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "daily_consumption_rate": {
                        "type": "number",
                        "description": "Units consumed per day."
                    },
                    "current_inventory": {
                        "type": "number",
                        "description": "Total units currently in stock."
                    },
                    "expected_delay_days": {
                        "type": "number",
                        "description": "Number of days the supplier is delayed."
                    }
                },
                "required": ["daily_consumption_rate", "current_inventory", "expected_delay_days"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_breaking_point_report",
            "description": "Synthesizes stress test data into a formalized breaking point summary.",
            "parameters": {
                "type": "object",
                "properties": {
                    "failed_nodes": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "days_to_stockout": {
                        "type": "number"
                    },
                    "system_status": {
                        "type": "string",
                        "description": "e.g., 'CRITICAL', 'STABLE', 'COMPROMISED'"
                    }
                },
                "required": ["failed_nodes", "days_to_stockout", "system_status"]
            }
        }
    }
]

async def run_capacity_stress_test(network_capacity: list, surge_multiplier: float) -> str:
    """Calculates which node breaks first under a volume surge."""
    try:
        broken_nodes = []
        survival_log = []
        
        for node in network_capacity:
            name = node.get("node_name", "Unknown")
            max_cap = node.get("max_capacity", 1)
            current_vol = node.get("current_volume", 0)
            
            stressed_vol = current_vol * surge_multiplier
            utilization = (stressed_vol / max_cap) * 100
            
            if utilization > 100:
                broken_nodes.append({
                    "node": name,
                    "overflow_amount": stressed_vol - max_cap,
                    "utilization_percent": f"{utilization:.1f}%"
                })
                survival_log.append(f"❌ {name} FAILED: Reached {utilization:.1f}% capacity. Overflow: {stressed_vol - max_cap:.1f} units.")
            else:
                survival_log.append(f"✅ {name} SURVIVED: Reached {utilization:.1f}% capacity. Remaining buffer: {max_cap - stressed_vol:.1f} units.")
                
        return json.dumps({
            "surge_applied": f"{surge_multiplier}x",
            "total_nodes_broken": len(broken_nodes),
            "broken_nodes_details": broken_nodes,
            "log": survival_log
        }, indent=2)
    except Exception as e:
        return f"Error running capacity stress test: {str(e)}"

async def simulate_lead_time_shock(daily_consumption_rate: float, current_inventory: float, expected_delay_days: float) -> str:
    """Calculates stockout horizon based on a sudden supply freeze."""
    try:
        if daily_consumption_rate <= 0:
            return "Error: Daily consumption rate must be > 0"
            
        days_of_buffer = current_inventory / daily_consumption_rate
        deficit_days = expected_delay_days - days_of_buffer
        
        if deficit_days <= 0:
            status = "SAFE"
            message = f"Inventory buffer ({days_of_buffer:.1f} days) is sufficient to absorb the {expected_delay_days}-day delay."
        else:
            status = "STOCKOUT_IMMINENT"
            message = f"Inventory will deplete in {days_of_buffer:.1f} days. The system will face a complete stockout for {deficit_days:.1f} days before the delayed supply arrives."
            
        return json.dumps({
            "current_buffer_days": float(f"{days_of_buffer:.1f}"),
            "expected_delay_days": expected_delay_days,
            "status": status,
            "analysis": message,
            "stockout_duration_days": float(f"{max(0, deficit_days):.1f}")
        }, indent=2)
    except Exception as e:
        return f"Error simulating lead time shock: {str(e)}"

async def generate_breaking_point_report(failed_nodes: list, days_to_stockout: float, system_status: str) -> str:
    """Formalizes the breaking point report."""
    return json.dumps({
        "report_type": "System Breaking Point Analysis",
        "overall_status": system_status,
        "structural_failures": failed_nodes if failed_nodes else ["None - Capacity limits held."],
        "time_to_system_halt": f"{days_to_stockout} days",
        "conclusion": f"The network's weakest link limits survivability to {days_to_stockout} days under extreme stress."
    }, indent=2)
