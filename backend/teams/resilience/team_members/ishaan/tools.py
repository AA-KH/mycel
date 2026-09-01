import json
import random

ISHAAN_SPECIFIC_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "simulate_cascading_failure",
            "description": "Simulates failure propagation in a supply chain network. If a node fails, its load shifts to connected nodes, potentially causing them to exceed capacity and fail.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nodes": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "capacity": {"type": "number", "description": "Maximum load the node can handle."},
                                "current_load": {"type": "number", "description": "Current active load on the node."}
                            },
                            "required": ["id", "capacity", "current_load"]
                        }
                    },
                    "edges": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "source": {"type": "string"},
                                "target": {"type": "string"}
                            },
                            "required": ["source", "target"]
                        }
                    },
                    "initial_failed_node": {
                        "type": "string",
                        "description": "The ID of the node that initially fails."
                    }
                },
                "required": ["nodes", "edges", "initial_failed_node"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_monte_carlo_simulation",
            "description": "Runs a Monte Carlo probability simulation to determine the statistical likelihood of supply chain collapse given various risks.",
            "parameters": {
                "type": "object",
                "properties": {
                    "risk_events": {
                        "type": "array",
                        "description": "List of risks with their probability and impact (0.0 to 1.0).",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "probability": {"type": "number", "description": "Chance of occurring (e.g. 0.15 for 15%)"},
                                "impact_severity": {"type": "number", "description": "Percentage of network disrupted if it occurs (e.g. 0.4 for 40%)"}
                            },
                            "required": ["name", "probability", "impact_severity"]
                        }
                    },
                    "iterations": {
                        "type": "integer",
                        "description": "Number of simulation runs. Default 1000."
                    }
                },
                "required": ["risk_events"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_black_swan_scenario",
            "description": "Logically constructs a highly unlikely but devastating multi-layered 'Black Swan' event for stress-testing.",
            "parameters": {
                "type": "object",
                "properties": {
                    "industry": {
                        "type": "string",
                        "description": "The industry to target (e.g. 'Semiconductors', 'Automotive')."
                    },
                    "region": {
                        "type": "string",
                        "description": "The geographical region (e.g. 'South China Sea', 'Europe')."
                    }
                },
                "required": ["industry", "region"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_nasa_eonet_anomalies",
            "description": "Fetches active extreme natural events (Wildfires, Volcanoes, Icebergs) from NASA EONET to ground Black Swan scenarios in reality.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Number of recent events to fetch. Default is 5."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_world_bank_economic_data",
            "description": "Fetches macroeconomic indicators (like GDP or Inflation) for a specific country to simulate economic collapse scenarios.",
            "parameters": {
                "type": "object",
                "properties": {
                    "country_code": {
                        "type": "string",
                        "description": "2-letter ISO country code (e.g., 'US', 'CN', 'IN')."
                    },
                    "indicator": {
                        "type": "string",
                        "description": "World Bank Indicator (e.g., 'FP.CPI.TOTL.ZG' for Inflation, 'NY.GDP.MKTP.CD' for GDP)."
                    }
                },
                "required": ["country_code", "indicator"]
            }
        }
    }
]

import os
import aiohttp

async def simulate_cascading_failure(nodes: list, edges: list, initial_failed_node: str) -> str:
    """Simulates a graph-based cascading failure."""
    try:
        node_map = {n['id']: n for n in nodes}
        if initial_failed_node not in node_map:
            return f"Error: Initial failed node '{initial_failed_node}' not found in nodes."
            
        failed_nodes = {initial_failed_node}
        propagation_log = [f"Time 0: {initial_failed_node} fails. Its load of {node_map[initial_failed_node]['current_load']} must be redistributed."]
        
        # Build adjacency list (undirected for load shifting)
        adj = {n['id']: [] for n in nodes}
        for edge in edges:
            src, tgt = edge['source'], edge['target']
            if src in adj and tgt in adj:
                adj[src].append(tgt)
                adj[tgt].append(src)
                
        # Simulate steps
        queue = [initial_failed_node]
        step = 1
        
        while queue:
            current = queue.pop(0)
            load_to_shift = node_map[current]['current_load']
            
            # Find surviving neighbors
            surviving_neighbors = [neighbor for neighbor in adj[current] if neighbor not in failed_nodes]
            
            if not surviving_neighbors:
                propagation_log.append(f"Time {step}: No surviving neighbors for {current}. Load is permanently lost.")
                continue
                
            load_per_neighbor = load_to_shift / len(surviving_neighbors)
            
            for neighbor in surviving_neighbors:
                node_map[neighbor]['current_load'] += load_per_neighbor
                # Check if it exceeds capacity
                if node_map[neighbor]['current_load'] > node_map[neighbor]['capacity']:
                    failed_nodes.add(neighbor)
                    queue.append(neighbor)
                    propagation_log.append(f"Time {step}: {neighbor} failed due to overload (Load: {node_map[neighbor]['current_load']:.1f}, Capacity: {node_map[neighbor]['capacity']}).")
                else:
                    propagation_log.append(f"Time {step}: {neighbor} absorbed {load_per_neighbor:.1f} load successfully.")
            step += 1
            
        return json.dumps({
            "initial_failure": initial_failed_node,
            "total_nodes_failed": len(failed_nodes),
            "network_collapse_percentage": (len(failed_nodes) / len(nodes)) * 100,
            "failed_nodes_list": list(failed_nodes),
            "event_log": propagation_log
        }, indent=2)
        
    except Exception as e:
        return f"Error running cascading failure simulation: {str(e)}"

async def run_monte_carlo_simulation(risk_events: list, iterations: int = 1000) -> str:
    """Runs a Monte Carlo probability simulation."""
    try:
        critical_failure_count = 0
        total_impact = 0.0
        
        # We consider a "critical failure" if combined impact > 0.7 (70% disruption)
        CRITICAL_THRESHOLD = 0.7
        
        for _ in range(iterations):
            run_impact = 0.0
            for risk in risk_events:
                # Roll a dice between 0 and 1
                roll = random.random()
                if roll < risk.get('probability', 0):
                    run_impact += risk.get('impact_severity', 0)
            
            total_impact += run_impact
            if run_impact >= CRITICAL_THRESHOLD:
                critical_failure_count += 1
                
        prob_of_critical_failure = (critical_failure_count / iterations) * 100
        avg_impact = (total_impact / iterations) * 100
        
        return json.dumps({
            "iterations": iterations,
            "critical_threshold": f"{CRITICAL_THRESHOLD * 100}% network damage",
            "probability_of_critical_collapse": f"{prob_of_critical_failure:.2f}%",
            "average_simulated_damage": f"{avg_impact:.2f}%",
            "insight": f"Out of {iterations} simulated futures, the supply chain fully collapsed {critical_failure_count} times."
        }, indent=2)
        
    except Exception as e:
        return f"Error running Monte Carlo simulation: {str(e)}"

async def generate_black_swan_scenario(industry: str, region: str) -> str:
    """Generates a structured Black Swan event logic tree."""
    # Since this relies on the LLM's own context in practice, this tool acts as a structured framer
    # rather than doing its own external API call (though it could).
    
    events = [
        "Unprecedented 1-in-500-year seismic event damaging underwater fiber cables and primary deepwater ports simultaneously.",
        "Coordinated zero-day ransomware attack on top 3 logistics providers combined with a massive dockworker strike.",
        "Sudden geopolitical embargo combined with a critical raw material export ban.",
        "Atmospheric river causing catastrophic flooding to major inland rail hubs while a category 5 hurricane hits coastal ports."
    ]
    
    selected_event = random.choice(events)
    
    return json.dumps({
        "industry_target": industry,
        "region_target": region,
        "black_swan_core_event": selected_event,
        "cascading_effects": [
            "Immediate halt of 80% of regional outbound shipments.",
            "Widespread panic buying causing artificial demand spikes of 400%.",
            "Communication blackouts preventing rerouting coordination."
        ],
        "financial_impact_estimate": "Catastrophic (Requires immediate intervention plan)"
    }, indent=2)

async def fetch_nasa_eonet_anomalies(limit: int = 5) -> str:
    """Fetches extreme environmental anomalies from NASA EONET."""
    try:
        url = f"https://eonet.gsfc.nasa.gov/api/v3/events?limit={limit}&status=open"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    return f"Error: NASA EONET API returned {response.status}"
                data = await response.json()
                
        events = []
        for event in data.get("events", []):
            events.append({
                "title": event.get("title"),
                "categories": [c.get("title") for c in event.get("categories", [])],
                "date": event.get("geometry", [{}])[0].get("date")
            })
            
        return json.dumps({
            "source": "NASA EONET",
            "active_anomalies": events,
            "insight": "Use these extreme events as the foundation for your Black Swan Scenario generation."
        }, indent=2)
    except Exception as e:
        return f"Error fetching NASA EONET data: {str(e)}"

async def fetch_world_bank_economic_data(country_code: str, indicator: str) -> str:
    """Fetches macroeconomic data from World Bank API."""
    try:
        # Example indicators: FP.CPI.TOTL.ZG (Inflation), NY.GDP.MKTP.CD (GDP)
        url = f"https://api.worldbank.org/v2/country/{country_code}/indicator/{indicator}?format=json&per_page=1"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    return f"Error: World Bank API returned {response.status}"
                data = await response.json()
                
        if len(data) > 1 and isinstance(data[1], list) and len(data[1]) > 0:
            latest_data = data[1][0]
            return json.dumps({
                "source": "World Bank API",
                "country": latest_data.get("country", {}).get("value"),
                "indicator": latest_data.get("indicator", {}).get("value"),
                "year": latest_data.get("date"),
                "value": latest_data.get("value"),
                "insight": "Use this economic baseline to simulate macroeconomic disruption scenarios."
            }, indent=2)
        else:
            return f"No recent data found for indicator {indicator} in country {country_code}."
            
    except Exception as e:
        return f"Error fetching World Bank data: {str(e)}"
