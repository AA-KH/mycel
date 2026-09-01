from teams.resilience.base import ResilienceBaseAgent
from teams.resilience.team_members.zoya.prompt import ZOYA_SYSTEM_PROMPT
from teams.resilience.team_members.zoya.tools import ZOYA_SPECIFIC_TOOLS, search_global_news, check_supplier_financial_health, analyze_geopolitical_risk, map_network_spof, calculate_fmea_rpn, fetch_global_disaster_alerts, check_severe_weather, fetch_conflict_events

class ZoyaAgent(ResilienceBaseAgent):
    def __init__(self, task_id: str = "default", session_id: str = None):
        # Zoya doesn't need heavy math reasoning, but she needs the ReAct base class.
        super().__init__(
            name="Zoya",
            role="Risk Analyst",
            system_prompt=ZOYA_SYSTEM_PROMPT,
            user_id=task_id,
            tools=ZOYA_SPECIFIC_TOOLS,
            session_id=session_id
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
        elif function_name == "map_network_spof":
            return await map_network_spof(
                arguments.get("nodes", []),
                arguments.get("edges", [])
            )
        elif function_name == "calculate_fmea_rpn":
            return await calculate_fmea_rpn(
                arguments.get("failure_mode", ""),
                arguments.get("severity", 1),
                arguments.get("occurrence", 1),
                arguments.get("detection", 1)
            )
        elif function_name == "fetch_global_disaster_alerts":
            return await fetch_global_disaster_alerts(
                arguments.get("alert_level", "Red,Orange")
            )
        elif function_name == "check_severe_weather":
            return await check_severe_weather(
                arguments.get("city", "")
            )
        elif function_name == "fetch_conflict_events":
            return await fetch_conflict_events(
                arguments.get("country", ""),
                arguments.get("limit", 5)
            )
        
        return await super().execute_tool(function_name, arguments)
