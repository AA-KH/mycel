import json
import httpx
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from ddgs import DDGS
from teams.architecture.base import ArchitectureBaseAgent
from .profile import NAME, ROLE
from .prompt import SYSTEM_PROMPT
from .tools import get_tools

class RohanAgent(ArchitectureBaseAgent):
    def __init__(self, session_id: str = None):
        super().__init__(
            name=NAME,
            role=ROLE,
            system_prompt=SYSTEM_PROMPT,
            agent_tools=get_tools(),
            session_id=session_id
        )

    async def execute_tool(self, function_name: str, arguments: dict):
        if function_name == "design_supply_chain_network":
            # Use Geopy for Real Distances
            geolocator = Nominatim(user_agent="mycel_supply_chain_agent")
            
            origin = arguments.get("origin_country")
            destination = arguments.get("destination_country")
            
            try:
                loc_origin = geolocator.geocode(origin)
                loc_dest = geolocator.geocode(destination)
                
                if loc_origin and loc_dest:
                    distance_km = geodesic((loc_origin.latitude, loc_origin.longitude), (loc_dest.latitude, loc_dest.longitude)).kilometers
                    # Assuming average sea freight speed of 37 km/h (20 knots)
                    real_sea_transit_days = round(distance_km / (37 * 24), 2)
                else:
                    distance_km = "Unknown"
                    real_sea_transit_days = arguments.get("estimated_lead_time_days", 0)
            except Exception as e:
                distance_km = "API Error"
                real_sea_transit_days = arguments.get("estimated_lead_time_days", 0)

            return json.dumps({
                "status": "success",
                "origin": origin,
                "destination": destination,
                "distance_km": round(distance_km, 2) if isinstance(distance_km, float) else distance_km,
                "estimated_sea_transit_days": real_sea_transit_days,
                "total_nodes": len(arguments.get("tier_1_suppliers", [])) + len(arguments.get("transit_nodes", [])),
                "insight": f"Calculated real-world geographic distance between {origin} and {destination}."
            })
            
        elif function_name == "simulate_bottleneck":
            failed_node = arguments.get("failed_node", "")
            downtime = arguments.get("downtime_days", 0)
            
            # Use Open-Meteo to check weather at the failed node
            weather_alert = "No severe weather currently."
            geolocator = Nominatim(user_agent="mycel_supply_chain_agent")
            
            try:
                loc = geolocator.geocode(failed_node)
                if loc:
                    async with httpx.AsyncClient() as client:
                        weather_res = await client.get(f"https://api.open-meteo.com/v1/forecast?latitude={loc.latitude}&longitude={loc.longitude}&current_weather=true")
                        if weather_res.status_code == 200:
                            current_weather = weather_res.json().get("current_weather", {})
                            wind_speed = current_weather.get("windspeed", 0)
                            if wind_speed > 60:
                                weather_alert = f"DANGER: High winds detected ({wind_speed} km/h) at {failed_node}. Port operations likely suspended."
            except Exception:
                pass
            
            # Use DuckDuckGo Search for live news
            recent_news = "No recent disruptions found."
            try:
                results = DDGS().text(f"{failed_node} port strike closure supply chain disruption", max_results=2)
                if results:
                    recent_news = [r.get('title') for r in results]
            except Exception:
                pass
                
            has_backup = arguments.get("has_backup_node", False)
            impact_score = downtime * (2 if not has_backup else 0.5)
            
            return json.dumps({
                "node_failed": failed_node,
                "live_weather_insight": weather_alert,
                "live_news_context": recent_news,
                "downtime_days": downtime,
                "impact_score": impact_score,
                "recommendation": "URGENT: Re-route shipments immediately." if impact_score > 10 or "DANGER" in weather_alert else "Monitor situation closely."
            })
            
        elif function_name == "generate_mermaid_graph":
            from teams.architecture.shared_tools import generate_mermaid_graph
            return await generate_mermaid_graph(
                arguments.get("graph_type", "flowchart"),
                arguments.get("elements", []),
                arguments.get("title", "Supply Chain Topology")
            )
        else:
            return f"Error: Tool '{function_name}' not recognized by RohanAgent."
