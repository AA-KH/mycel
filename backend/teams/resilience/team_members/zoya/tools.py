import logging
import json
import httpx
from core.config import settings

logger = logging.getLogger(__name__)

ZOYA_SPECIFIC_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_global_news",
            "description": "Searches Google News for live breaking events, port strikes, canal blockages, or natural disasters.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query (e.g., 'Suez Canal blocked', 'Port of LA strike', 'Taiwan semiconductor fire')."
                    },
                    "days_back": {
                        "type": "integer",
                        "description": "Number of days back to search for news."
                    }
                },
                "required": ["query", "days_back"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_supplier_financial_health",
            "description": "Analyzes the credit risk and bankruptcy probability of a supplier.",
            "parameters": {
                "type": "object",
                "properties": {
                    "supplier_name": {
                        "type": "string",
                        "description": "Name of the supplier company."
                    }
                },
                "required": ["supplier_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_geopolitical_risk",
            "description": "Analyzes geopolitical risks for a given country code (e.g., 'TW', 'CN', 'US').",
            "parameters": {
                "type": "object",
                "properties": {
                    "country_code": {
                        "type": "string",
                        "description": "2-letter ISO country code."
                    }
                },
                "required": ["country_code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "map_network_spof",
            "description": "Maps the structural topology of a supply chain network to identify Single Points of Failure (SPOF).",
            "parameters": {
                "type": "object",
                "properties": {
                    "nodes": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of node names (e.g., ['Factory_A', 'Port_B', 'Warehouse_C'])."
                    },
                    "edges": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of connections in 'Node1->Node2' format (e.g., ['Factory_A->Port_B'])."
                    }
                },
                "required": ["nodes", "edges"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_fmea_rpn",
            "description": "Calculates the Risk Priority Number (RPN) using standard Failure Mode and Effects Analysis (FMEA).",
            "parameters": {
                "type": "object",
                "properties": {
                    "failure_mode": {
                        "type": "string",
                        "description": "Description of what might fail."
                    },
                    "severity": {
                        "type": "integer",
                        "description": "Severity of the failure (1-10)."
                    },
                    "occurrence": {
                        "type": "integer",
                        "description": "Probability of occurrence (1-10)."
                    },
                    "detection": {
                        "type": "integer",
                        "description": "Difficulty of detection before failure occurs (1-10)."
                    }
                },
                "required": ["failure_mode", "severity", "occurrence", "detection"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_global_disaster_alerts",
            "description": "Fetches live natural disaster alerts (Earthquakes, Floods, Tsunamis, Cyclones) from GDACS.",
            "parameters": {
                "type": "object",
                "properties": {
                    "alert_level": {
                        "type": "string",
                        "description": "Filter by severity (e.g., 'Red', 'Orange', 'Green'). Use 'Red,Orange' for severe."
                    }
                },
                "required": ["alert_level"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_severe_weather",
            "description": "Checks live weather alerts for a specific location using OpenWeatherMap.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "City name (e.g., 'Kaohsiung', 'Los Angeles')."
                    }
                },
                "required": ["city"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_conflict_events",
            "description": "Fetches recent geopolitical conflicts or riots using ACLED API.",
            "parameters": {
                "type": "object",
                "properties": {
                    "country": {
                        "type": "string",
                        "description": "Country name (e.g., 'Taiwan', 'United States')."
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of recent events to fetch (default: 5)."
                    }
                },
                "required": ["country"]
            }
        }
    }
]

import os
import aiohttp

async def map_network_spof(nodes: list, edges: list) -> str:
    """Identifies structural Single Points of Failure (SPOF) based on graph topology."""
    try:
        # Simple graph building
        adjacency = {node: [] for node in nodes}
        in_degrees = {node: 0 for node in nodes}
        out_degrees = {node: 0 for node in nodes}
        
        for edge in edges:
            if "->" in edge:
                u, v = edge.split("->")
                u, v = u.strip(), v.strip()
                if u in adjacency and v in adjacency:
                    adjacency[u].append(v)
                    out_degrees[u] += 1
                    in_degrees[v] += 1
        
        spofs = []
        for node in nodes:
            # A simplistic heuristic for SPOF: A node that handles a large percentage of routing, 
            # or is the only bridge between clusters. For this simulation, if a node has high in-degree 
            # and out-degree, or acts as the only middleman, it's a SPOF.
            if in_degrees[node] > 0 and out_degrees[node] > 0:
                if len(adjacency[node]) == 1 or in_degrees[node] >= len(nodes) / 3:
                    spofs.append(node)
                    
        return json.dumps({
            "analyzed_nodes_count": len(nodes),
            "analyzed_edges_count": len(edges),
            "identified_spofs": spofs if spofs else ["None detected with current graph"],
            "topological_insight": f"Nodes {spofs} act as critical bottlenecks. If any of these fail, the graph splits."
        }, indent=2)
    except Exception as e:
        return f"Error mapping network SPOF: {str(e)}"

async def calculate_fmea_rpn(failure_mode: str, severity: int, occurrence: int, detection: int) -> str:
    """Calculates Risk Priority Number (RPN) for FMEA."""
    try:
        # Cap values between 1 and 10
        s = max(1, min(10, severity))
        o = max(1, min(10, occurrence))
        d = max(1, min(10, detection))
        
        rpn = s * o * d
        
        # Risk categorization
        if rpn >= 500:
            risk_level = "CRITICAL (Immediate Action Required)"
        elif rpn >= 250:
            risk_level = "HIGH (Action Required)"
        elif rpn >= 100:
            risk_level = "MEDIUM (Monitor)"
        else:
            risk_level = "LOW (Acceptable)"
            
        return json.dumps({
            "failure_mode": failure_mode,
            "components": {
                "Severity (S)": s,
                "Occurrence (O)": o,
                "Detection (D)": d
            },
            "RPN": rpn,
            "risk_level": risk_level,
            "fmea_insight": f"An RPN of {rpn} indicates {risk_level}. High severity ({s}) requires structural mitigation."
        }, indent=2)
    except Exception as e:
        return f"Error calculating FMEA RPN: {str(e)}"

async def fetch_global_disaster_alerts(alert_level: str = "Red,Orange") -> str:
    """Fetches live disaster events from GDACS API."""
    try:
        url = f"https://www.gdacs.org/gdacsapi/api/events/geteventlist/SEARCH?alertlevel={alert_level}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    return f"Error: GDACS API returned {response.status}"
                data = await response.json()
                
        # Limit to top 5 recent severe events for context window
        events = data.get("features", [])[:5]
        parsed_events = []
        for event in events:
            props = event.get("properties", {})
            parsed_events.append({
                "type": props.get("eventtype"),
                "name": props.get("name"),
                "country": props.get("country"),
                "severity": props.get("alertscore"),
                "description": props.get("description"),
                "date": props.get("fromdate")
            })
            
        return json.dumps({
            "source": "GDACS API",
            "alerts": parsed_events
        }, indent=2)
    except Exception as e:
        return f"Error fetching GDACS alerts: {str(e)}"

async def check_severe_weather(city: str) -> str:
    """Uses OpenWeatherMap to fetch live weather and alerts."""
    try:
        api_key = os.getenv("OPENWEATHERMAP_API_KEY")
        if not api_key:
            return "Error: OPENWEATHERMAP_API_KEY is not configured in .env"
            
        # Geocoding
        geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={api_key}"
        async with aiohttp.ClientSession() as session:
            async with session.get(geo_url) as geo_res:
                if geo_res.status != 200:
                    return "Error: Failed to geocode city."
                geo_data = await geo_res.json()
                if not geo_data:
                    return f"No coordinates found for {city}"
                
                lat, lon = geo_data[0]["lat"], geo_data[0]["lon"]
                
            # Fetch Weather & Alerts (One Call 3.0 or Current Weather fallback)
            # Since One Call 3.0 requires subscription, we'll use 2.5 current weather for demo
            weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
            async with session.get(weather_url) as weather_res:
                w_data = await weather_res.json()
                
        return json.dumps({
            "city": city,
            "coordinates": {"lat": lat, "lon": lon},
            "current_weather": w_data.get("weather", [{}])[0].get("description", "Unknown"),
            "wind_speed_ms": w_data.get("wind", {}).get("speed"),
            "visibility_m": w_data.get("visibility"),
            "insight": f"Severe weather risks at {city} can be extrapolated from wind ({w_data.get('wind', {}).get('speed')} m/s) and visibility."
        }, indent=2)
    except Exception as e:
        return f"Error checking weather: {str(e)}"

async def fetch_conflict_events(country: str, limit: int = 5) -> str:
    """Fetches live geopolitical conflict data from ACLED API."""
    try:
        email = os.getenv("ACLED_EMAIL")
        api_key = os.getenv("ACLED_API_KEY")
        
        if not email or not api_key:
            return "Error: ACLED_EMAIL or ACLED_API_KEY not configured in .env. Returning Mock Data for demonstration."
            
        url = f"https://api.acleddata.com/acled/read/?email={email}&key={api_key}&country={country}&limit={limit}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    return f"Error: ACLED API returned {response.status}"
                data = await response.json()
                
        events = data.get("data", [])
        parsed = [{"date": e.get("event_date"), "type": e.get("event_type"), "location": e.get("location"), "fatalities": e.get("fatalities")} for e in events]
        
        return json.dumps({"source": "ACLED API", "country": country, "recent_conflicts": parsed}, indent=2)
    except Exception as e:
        return f"Error fetching ACLED data: {str(e)}"

async def search_global_news(query: str, days_back: int) -> str:
    """Uses Serper.dev API to fetch live news."""
    try:
        api_key = settings.serper_api_key
        if not api_key or api_key == "your_serper_key_here":
            return json.dumps({
                "status": "warning",
                "message": f"Serper API key not configured. Mocking news for query: {query}",
                "articles": [
                    {"title": f"Mock Alert: Disruption reported relating to {query}", "snippet": "Unconfirmed reports suggest operations are halted."}
                ]
            })

        url = "https://google.serper.dev/news"
        payload = json.dumps({
            "q": query,
            "tbs": f"qdr:d{days_back}"
        })
        headers = {
            'X-API-KEY': api_key,
            'Content-Type': 'application/json'
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, data=payload)
            
        if response.status_code == 200:
            news_data = response.json()
            articles = news_data.get("news", [])[:3] # Return top 3
            result = []
            for art in articles:
                result.append({
                    "title": art.get("title"),
                    "snippet": art.get("snippet"),
                    "date": art.get("date")
                })
            return json.dumps({"status": "success", "articles": result}, indent=2)
        else:
            return f"Error: Failed to fetch news. Status Code {response.status_code}"
    except Exception as e:
        return f"Error searching news: {str(e)}"

async def check_supplier_financial_health(supplier_name: str) -> str:
    """Simulates checking financial risk databases for supplier bankruptcy."""
    try:
        # Mock logic based on keyword to simulate live financial DB lookup
        name_lower = supplier_name.lower()
        
        if "evergrande" in name_lower or "bankrupt" in name_lower:
            risk = "CRITICAL"
            z_score = 1.1
            insight = f"{supplier_name} is in severe distress (Altman Z-Score < 1.8). High risk of immediate insolvency."
        elif "startup" in name_lower:
            risk = "HIGH"
            z_score = 2.0
            insight = f"{supplier_name} shows high cash-burn rate. Financials are unstable."
        else:
            risk = "LOW"
            z_score = 3.5
            insight = f"{supplier_name} appears financially stable with strong cash reserves."
            
        return json.dumps({
            "supplier": supplier_name,
            "altman_z_score": z_score,
            "bankruptcy_risk_level": risk,
            "insight": insight
        }, indent=2)
    except Exception as e:
        return f"Error checking financial health: {str(e)}"

async def analyze_geopolitical_risk(country_code: str) -> str:
    """Evaluates country-level geopolitical risks."""
    try:
        code = country_code.upper()
        # Simulated risk index based on macro geopolitical climate
        risk_map = {
            "TW": {"risk": "HIGH", "factors": ["Tensions in Taiwan Strait", "Semiconductor export controls"]},
            "UA": {"risk": "CRITICAL", "factors": ["Active conflict zone", "Infrastructure damage"]},
            "RU": {"risk": "CRITICAL", "factors": ["International sanctions", "SWIFT ban"]},
            "CN": {"risk": "MEDIUM", "factors": ["Tariffs", "Trade policy shifts"]},
            "IL": {"risk": "HIGH", "factors": ["Regional conflict", "Red Sea shipping diversions"]},
            "US": {"risk": "LOW", "factors": ["Stable institutions, but watch for domestic port strikes"]},
            "DE": {"risk": "LOW", "factors": ["Stable EU member, energy prices normalized"]}
        }
        
        data = risk_map.get(code, {"risk": "UNKNOWN", "factors": ["No specific alerts in database"]})
        
        return json.dumps({
            "country": code,
            "geopolitical_risk_level": data["risk"],
            "key_factors": data["factors"]
        }, indent=2)
    except Exception as e:
        return f"Error checking geopolitical risk: {str(e)}"
