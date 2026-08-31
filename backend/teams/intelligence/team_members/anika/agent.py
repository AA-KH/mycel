from teams.intelligence.base import IntelligenceBaseAgent, INTELLIGENCE_TOOLS, ELITE_REASONING_INSTRUCTIONS
from teams.intelligence.team_members.anika.tools import fetch_competitor_metrics, analyze_industry_trends

# --- ANIKA SPECIFIC TOOLS ---
ANIKA_SPECIFIC_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "fetch_competitor_metrics",
            "description": "Fetches real-world financial metrics (Gross Margins, Revenue) for a competitor using Yahoo Finance. Use this to verify if a competitor is actually financially efficient.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "The stock ticker of the competitor (e.g., 'AAPL', 'TSLA', 'AMZN')"
                    }
                },
                "required": ["ticker"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_industry_trends",
            "description": "Searches for high-level consulting reports (McKinsey, Gartner, Bain) to determine true industry supply chain standards and best practices.",
            "parameters": {
                "type": "object",
                "properties": {
                    "industry": {
                        "type": "string",
                        "description": "The industry to benchmark (e.g., 'Automotive', 'Consumer Electronics')"
                    }
                },
                "required": ["industry"]
            }
        }
    }
]

ANIKA_PROMPT = f"""You are Anika, the elite Industry & Supply-Chain Benchmarking Agent at Mycel's Supply Chain Division.
Your goal is to analyze competitor supply chains, find the industry's absolute best practices, and perform Gap Analysis.

{ELITE_REASONING_INSTRUCTIONS}

Anika's Specific Analytical Framework (Gap Analysis):
1. Financial Reality Check: Never assume a competitor has a good supply chain just because they are famous. Use `fetch_competitor_metrics` to check their actual Gross Margins. If margins are low, their supply chain is likely inefficient.
2. Consulting-Grade Insights: Use `analyze_industry_trends` to read actual McKinsey/Gartner reports on what the top 1% of the industry is doing.
3. Extreme Conditions Check: Identify how the industry standard fails during Black Swan events (e.g., how "Just-In-Time" failed during the COVID chip shortage).

Instructions:
1. Benchmark the requested supply chain against top competitors.
2. Use your tools (`fetch_competitor_metrics`, `analyze_industry_trends`, `web_search`) extensively to gather hard financial facts and consulting insights.
3. Always return a strictly formatted JSON output containing:
   - benchmark_companies (with their actual financial efficiency metrics)
   - industry_standard_margins
   - key_differentiators (what the top 1% do differently)
   - extreme_condition_weaknesses (where the industry standard fails)
Do not wrap the JSON in markdown blocks like ```json, just return the raw JSON string.
"""

class AnikaAgent(IntelligenceBaseAgent):
    def __init__(self, task_id: str, user_id: str = "system"):
        # Anika gets the common tools + her specialized benchmarking tools
        super().__init__(
            name="Anika", 
            role="industry_benchmarking", 
            system_prompt=ANIKA_PROMPT, 
            user_id=user_id, 
            tools=INTELLIGENCE_TOOLS + ANIKA_SPECIFIC_TOOLS
        )
        self.task_id = task_id

    async def execute_tool(self, function_name: str, arguments: dict) -> str:
        # Check Anika's specific tools first
        if function_name == "fetch_competitor_metrics":
            return await fetch_competitor_metrics(arguments.get("ticker", ""))
        elif function_name == "analyze_industry_trends":
            return await analyze_industry_trends(arguments.get("industry", ""))
        
        # Fallback to shared tools
        return await super().execute_tool(function_name, arguments)
