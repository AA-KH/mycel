from teams.council.base import CouncilBaseAgent
from teams.council.team_members.vikram.prompt import VIKRAM_SYSTEM_PROMPT
from teams.council.team_members.vikram.tools import (
    VIKRAM_SPECIFIC_TOOLS,
    fetch_active_disaster_alerts,
    score_supply_chain_resilience,
    map_single_points_of_failure,
    analyze_geographic_concentration,
    calculate_business_impact_of_failure,
    assess_recovery_readiness,
    fetch_country_political_stability
)

class VikramAgent(CouncilBaseAgent):
    def __init__(self, task_id: str = "default"):
        super().__init__(
            name="Vikram",
            role="Resilience Strategist (Council)",
            system_prompt=VIKRAM_SYSTEM_PROMPT,
            tools=VIKRAM_SPECIFIC_TOOLS,
            user_id=task_id
        )

    async def execute_tool(self, function_name: str, arguments: dict):
        if function_name == "fetch_active_disaster_alerts":
            return await fetch_active_disaster_alerts(
                arguments.get("alert_level", "red")
            )
        elif function_name == "score_supply_chain_resilience":
            return await score_supply_chain_resilience(
                arguments.get("product_category", ""),
                arguments.get("num_active_suppliers", 1),
                arguments.get("num_countries_sourced_from", 1),
                arguments.get("avg_lead_time_days", 30.0),
                arguments.get("safety_stock_days", 0.0),
                arguments.get("single_source_pct", 100.0)
            )
        elif function_name == "map_single_points_of_failure":
            return await map_single_points_of_failure(
                arguments.get("supply_chain_name", ""),
                arguments.get("nodes", [])
            )
        elif function_name == "analyze_geographic_concentration":
            return await analyze_geographic_concentration(
                arguments.get("supply_chain_name", ""),
                arguments.get("regional_breakdown", [])
            )
        elif function_name == "calculate_business_impact_of_failure":
            return await calculate_business_impact_of_failure(
                arguments.get("node_name", ""),
                arguments.get("daily_revenue_at_risk_usd", 0.0),
                arguments.get("estimated_downtime_days", 0.0),
                arguments.get("emergency_sourcing_cost_usd", 0.0),
                arguments.get("customer_penalty_clauses_usd", 0.0),
                arguments.get("reputational_impact_multiplier", 1.0)
            )
        elif function_name == "assess_recovery_readiness":
            return await assess_recovery_readiness(
                arguments.get("supply_chain_name", ""),
                arguments.get("has_documented_bcp", False),
                arguments.get("backup_supplier_qualification_days", 90),
                arguments.get("current_safety_stock_days", 0.0),
                arguments.get("last_bcp_test_months_ago", 999),
                arguments.get("has_dual_sourcing_contracts", False),
                arguments.get("logistics_alternative_available", False)
            )
        elif function_name == "fetch_country_political_stability":
            return await fetch_country_political_stability(
                arguments.get("country_code", ""),
                arguments.get("country_name", "")
            )

        # Fall through to shared Council tools
        return await super().execute_tool(function_name, arguments)
