from teams.council.base import CouncilBaseAgent
from teams.council.team_members.helena.prompt import HELENA_SYSTEM_PROMPT
from teams.council.team_members.helena.tools import (
    HELENA_SPECIFIC_TOOLS,
    benchmark_supplier_cost,
    fetch_commodity_price,
    calculate_total_cost_of_ownership,
    analyze_spend_concentration,
    optimize_payment_terms,
    convert_supplier_quote_to_usd,
    check_country_inflation_risk
)

class HelenaAgent(CouncilBaseAgent):
    def __init__(self, task_id: str = "default"):
        super().__init__(
            name="Helena",
            role="Cost Strategist (Council)",
            system_prompt=HELENA_SYSTEM_PROMPT,
            tools=HELENA_SPECIFIC_TOOLS,
            user_id=task_id
        )

    async def execute_tool(self, function_name: str, arguments: dict):
        if function_name == "benchmark_supplier_cost":
            return await benchmark_supplier_cost(
                arguments.get("supplier_name", ""),
                arguments.get("product_category", ""),
                arguments.get("quoted_price_per_unit", 0.0),
                arguments.get("volume_units_per_year", 0.0)
            )
        elif function_name == "fetch_commodity_price":
            return await fetch_commodity_price(
                arguments.get("commodity", "")
            )
        elif function_name == "calculate_total_cost_of_ownership":
            return await calculate_total_cost_of_ownership(
                arguments.get("supplier_name", ""),
                arguments.get("unit_price_usd", 0.0),
                arguments.get("annual_volume_units", 0.0),
                arguments.get("freight_cost_per_unit_usd", 0.0),
                arguments.get("defect_rate_pct", 0.0),
                arguments.get("rework_cost_per_unit_usd", 0.0),
                arguments.get("avg_lead_time_days", 30.0),
                arguments.get("unit_holding_cost_per_day_usd", 0.0),
                arguments.get("switching_cost_one_time_usd", 0.0)
            )
        elif function_name == "analyze_spend_concentration":
            return await analyze_spend_concentration(
                arguments.get("category", ""),
                arguments.get("total_category_spend_usd", 0.0),
                arguments.get("supplier_spend_breakdown", [])
            )
        elif function_name == "optimize_payment_terms":
            return await optimize_payment_terms(
                arguments.get("supplier_name", ""),
                arguments.get("annual_spend_usd", 0.0),
                arguments.get("current_payment_days", 30),
                arguments.get("early_payment_discount_pct", 0.0),
                arguments.get("early_payment_days", 10),
                arguments.get("cost_of_capital_pct", 8.0)
            )
        elif function_name == "convert_supplier_quote_to_usd":
            return await convert_supplier_quote_to_usd(
                arguments.get("supplier_name", ""),
                arguments.get("quoted_amount", 0.0),
                arguments.get("source_currency", "USD")
            )
        elif function_name == "check_country_inflation_risk":
            return await check_country_inflation_risk(
                arguments.get("country_code", ""),
                arguments.get("country_name", ""),
                arguments.get("contract_duration_years", 1)
            )

        # Fall through to shared Council tools
        return await super().execute_tool(function_name, arguments)
