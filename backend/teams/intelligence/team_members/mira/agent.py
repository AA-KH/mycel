from teams.intelligence.base import IntelligenceBaseAgent, INTELLIGENCE_TOOLS, ELITE_REASONING_INSTRUCTIONS
from teams.intelligence.team_members.mira.tools import fetch_trend_data, get_economic_indicators

# --- MIRA SPECIFIC TOOLS ---
MIRA_SPECIFIC_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "fetch_trend_data",
            "description": "Fetches Google Trends and Social Media sentiment data for a keyword to identify if demand is real or just internet hype.",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "The product or market keyword (e.g. 'EV battery')"
                    }
                },
                "required": ["keyword"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_economic_indicators",
            "description": "Fetches macro-economic indicators (CPI, Inflation, Purchasing Power) for a specific region.",
            "parameters": {
                "type": "object",
                "properties": {
                    "region": {
                        "type": "string",
                        "description": "The region to analyze (e.g. 'Europe', 'US', 'Asia')"
                    }
                },
                "required": ["region"]
            }
        }
    }
]

MIRA_PROMPT = f"""You are Mira, the elite Market & Demand Intelligence Agent at Mycel's Supply Chain Division.
You operate with a McKinsey-level analytical mindset. You do not just report numbers; you uncover the truth behind the numbers.

{ELITE_REASONING_INSTRUCTIONS}

Mira's Specific Analytical Framework:
1. Hype vs Reality: Use `fetch_trend_data` to cross-check if the news sentiment matches actual consumer search volume and social trends.
2. Macroeconomic Reality: Use `get_economic_indicators` to verify if consumers in the target region actually have the purchasing power right now. If inflation is high, demand for non-essentials will plummet regardless of search volume.
3. Synthesis: Blend web search news, trend data, and economic reality to form your final conclusion.

Instructions:
1. Analyze the user's request.
2. Use your tools (`web_search`, `fetch_trend_data`, `get_economic_indicators`) extensively before making a decision.
3. Always return a strictly formatted JSON output containing:
   - target_demographics
   - key_competitors
   - expected_demand_volume
   - market_trends
   - hype_vs_reality_score (0-100)
   - macroeconomic_risk_factor (Low, Medium, High)
Do not wrap the JSON in markdown blocks like ```json, just return the raw JSON string.
"""

class MiraAgent(IntelligenceBaseAgent):
    def __init__(self, task_id: str, user_id: str = "system"):
        super().__init__(
            name="Mira", 
            role="market_intelligence", 
            system_prompt=MIRA_PROMPT, 
            user_id=user_id,
            tools=INTELLIGENCE_TOOLS + MIRA_SPECIFIC_TOOLS
        )
        self.task_id = task_id

    async def execute_tool(self, function_name: str, arguments: dict) -> str:
        # Check Mira's specific tools first
        if function_name == "fetch_trend_data":
            return await fetch_trend_data(arguments.get("keyword", ""))
        elif function_name == "get_economic_indicators":
            return await get_economic_indicators(arguments.get("region", ""))
        
        # Fallback to shared tools
        return await super().execute_tool(function_name, arguments)
