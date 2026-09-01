from teams.council.base import CouncilBaseAgent
from teams.council.team_members.omar.prompt import OMAR_SYSTEM_PROMPT
from teams.council.team_members.omar.tools import (
    OMAR_SPECIFIC_TOOLS,
    fetch_anti_corruption_index,
    screen_for_sanctions_and_aml,
    audit_gdpr_data_residency,
    audit_esg_and_labor_compliance,
    calculate_regulatory_fines_exposure
)

class OmarAgent(CouncilBaseAgent):
    def __init__(self, task_id: str = "default"):
        super().__init__(
            name="Omar",
            role="Risk & Compliance Strategist (Council)",
            system_prompt=OMAR_SYSTEM_PROMPT,
            tools=OMAR_SPECIFIC_TOOLS,
            user_id=task_id
        )

    async def execute_tool(self, function_name: str, arguments: dict):
        if function_name == "fetch_anti_corruption_index":
            return await fetch_anti_corruption_index(
                arguments.get("country_name", "")
            )
        elif function_name == "screen_for_sanctions_and_aml":
            return await screen_for_sanctions_and_aml(
                arguments.get("vendor_name", ""),
                arguments.get("operating_countries", []),
                arguments.get("has_pep_exposure", False)
            )
        elif function_name == "audit_gdpr_data_residency":
            return await audit_gdpr_data_residency(
                arguments.get("system_name", ""),
                arguments.get("processes_eu_pii", False),
                arguments.get("data_hosting_country", ""),
                arguments.get("has_scc_agreements", False),
                arguments.get("has_dpia_completed", False)
            )
        elif function_name == "audit_esg_and_labor_compliance":
            return await audit_esg_and_labor_compliance(
                arguments.get("vendor_name", ""),
                arguments.get("industry", ""),
                arguments.get("country", ""),
                arguments.get("has_conflict_minerals_declaration", False),
                arguments.get("has_reach_rohs_certification", False),
                arguments.get("has_third_party_labor_audit", False)
            )
        elif function_name == "calculate_regulatory_fines_exposure":
            return await calculate_regulatory_fines_exposure(
                arguments.get("company_global_revenue_usd", 0.0),
                arguments.get("gdpr_violation_flag", False),
                arguments.get("fcpa_violation_flag", False),
                arguments.get("sanctions_violation_flag", False),
                arguments.get("number_of_incidents", 1)
            )

        # Fall through to shared Council tools
        return await super().execute_tool(function_name, arguments)
