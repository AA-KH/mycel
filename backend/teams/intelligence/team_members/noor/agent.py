from teams.intelligence.base import IntelligenceBaseAgent, INTELLIGENCE_TOOLS, ELITE_REASONING_INSTRUCTIONS
from teams.intelligence.team_members.noor.tools import monitor_geopolitical_risk, analyze_environmental_disasters

# --- NOOR SPECIFIC TOOLS ---
NOOR_SPECIFIC_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "monitor_geopolitical_risk",
            "description": "Scans global news for military, political, or trade embargo threats in a specific region or chokepoint (e.g., 'Suez Canal', 'Taiwan', 'Middle East').",
            "parameters": {
                "type": "object",
                "properties": {
                    "region": {
                        "type": "string",
                        "description": "The geographical region or trade route to monitor."
                    }
                },
                "required": ["region"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_environmental_disasters",
            "description": "Scans global news for natural disasters, extreme weather, or port closures in a specific region (e.g., 'Florida', 'Shanghai').",
            "parameters": {
                "type": "object",
                "properties": {
                    "region": {
                        "type": "string",
                        "description": "The geographical region or port city to monitor."
                    }
                },
                "required": ["region"]
            }
        }
    }
]

NOOR_PROMPT = f"""You are Noor, the elite Geopolitical & External Risk Intelligence Agent at Mycel's Supply Chain Division.
Your absolute priority is to detect and prevent supply chain catastrophic failures caused by Black Swan events (wars, disasters, blockades).

{ELITE_REASONING_INSTRUCTIONS}

Noor's Specific Analytical Framework (Zero-Trust Logistics):
1. Assume the Supply Chain is Broken: You must treat every region and trade route as vulnerable until proven safe.
2. Dual-Threat Analysis: For any given region or trade route, you MUST check BOTH `monitor_geopolitical_risk` AND `analyze_environmental_disasters`. A route safe from war might be currently destroyed by a hurricane.
3. Identify Chokepoints: Break down the requested supply chain into geographical chokepoints (e.g., Panama Canal, Malacca Strait) and actively monitor those specific chokepoints.

Instructions:
1. Analyze the regions involved in the supply chain request.
2. Use your risk monitoring tools extensively to gather breaking threat intelligence.
3. Always return a strictly formatted JSON output containing:
   - critical_chokepoints (list of geographical vulnerabilities)
   - active_geopolitical_risks (detailed summary of wars, tariffs, blockades)
   - active_environmental_risks (detailed summary of weather/disasters)
   - overall_route_safety_score (0-100, where 100 is perfectly safe)
   - recommended_mitigations
Do not wrap the JSON in markdown blocks like ```json, just return the raw JSON string.
"""

class NoorAgent(IntelligenceBaseAgent):
    def __init__(self, task_id: str = "default", user_id: str = "system", session_id: str = None):
        # Noor gets the common tools + her specialized risk tools
        super().__init__(
            name="Noor", 
            role="geopolitical_risk", 
            system_prompt=NOOR_PROMPT, 
            user_id=user_id, 
            tools=INTELLIGENCE_TOOLS + NOOR_SPECIFIC_TOOLS,
            session_id=session_id
        )
        self.task_id = task_id

    async def execute_tool(self, function_name: str, arguments: dict) -> str:
        # Check Noor's specific tools first
        if function_name == "monitor_geopolitical_risk":
            return await monitor_geopolitical_risk(arguments.get("region", ""))
        elif function_name == "analyze_environmental_disasters":
            return await analyze_environmental_disasters(arguments.get("region", ""))
        
        # Fallback to shared tools
        return await super().execute_tool(function_name, arguments)
