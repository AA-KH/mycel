from teams.network.base import NetworkBaseAgent
from teams.network.resilience.zoya.prompt import ZOYA_SYSTEM_PROMPT
from teams.network.resilience.zoya.tools import ZOYA_SPECIFIC_TOOLS, search_global_news, check_supplier_financial_health, analyze_geopolitical_risk

class ZoyaAgent(NetworkBaseAgent):
    def __init__(self, task_id: str = "default"):
        # Zoya doesn't need heavy math reasoning, but she needs the ReAct base class.
        super().__init__(
            name="Zoya",
            role="Risk Analyst",
            system_prompt=ZOYA_SYSTEM_PROMPT,
            user_id=task_id,
            tools=ZOYA_SPECIFIC_TOOLS
        )
        
    async def execute_tool(self, function_name: str, arguments: dict) -> str:
        if function_name == "search_global_news":
            return await search_global_news(
                arguments.get("query", ""),
                arguments.get("days_back", 7)
            )
        elif function_name == "check_supplier_financial_health":
            return await check_supplier_financial_health(
                arguments.get("supplier_name", "")
            )
        elif function_name == "analyze_geopolitical_risk":
            return await analyze_geopolitical_risk(
                arguments.get("country_code", "")
            )
        
        return await super().execute_tool(function_name, arguments)
