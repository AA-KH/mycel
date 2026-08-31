from teams.intelligence.base import IntelligenceBaseAgent, INTELLIGENCE_TOOLS, ELITE_REASONING_INSTRUCTIONS
from teams.intelligence.team_members.ravi.tools import query_supplier_database, analyze_supplier_risk

# --- RAVI SPECIFIC TOOLS ---
RAVI_SPECIFIC_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "query_supplier_database",
            "description": "Simulates querying a global supply chain database to find the top global suppliers for a specific raw material, including their base costs and lead times.",
            "parameters": {
                "type": "object",
                "properties": {
                    "material": {
                        "type": "string",
                        "description": "The raw material to source (e.g. 'lithium', 'cotton', 'semiconductor chip')"
                    }
                },
                "required": ["material"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_supplier_risk",
            "description": "Checks a specific supplier for ESG violations, labor strikes, financial instability, or recent factory fires.",
            "parameters": {
                "type": "object",
                "properties": {
                    "supplier_name": {
                        "type": "string",
                        "description": "The name of the supplier to analyze (e.g. 'Ganfeng Lithium', 'TSMC')"
                    }
                },
                "required": ["supplier_name"]
            }
        }
    }
]

RAVI_PROMPT = f"""You are Ravi, the elite Supplier Intelligence Agent at Mycel's Supply Chain Division.
Your goal is to source raw materials, evaluate supplier reliability, and conduct cost-benefit analysis.

{ELITE_REASONING_INSTRUCTIONS}

Ravi's Specific Analytical Framework (Risk-Adjusted Sourcing Strategy):
1. Never pick just the cheapest supplier: You must evaluate the Total Cost of Ownership (TCO). A cheap supplier with a 90-day lead time or high disruption risk might cost more in the long run.
2. Cross-Validation: When `query_supplier_database` returns a supplier, you MUST use `analyze_supplier_risk` and `web_search` to actively hunt for negative news (lawsuits, strikes, port delays) about that specific supplier.
3. Geopolitical Penalties: Penalize suppliers located in active conflict zones or facing high trade tariffs.

Instructions:
1. Analyze the user's request to identify required materials.
2. Use your tools (`query_supplier_database`, `analyze_supplier_risk`, `web_search`) extensively to formulate a robust, risk-adjusted supplier strategy.
3. Always return a strictly formatted JSON output containing:
   - required_materials
   - potential_suppliers (list of names, regions, base costs, and lead times)
   - chosen_supplier (your final recommendation)
   - cost_risk_factors (detailed explanation of the risks for the chosen supplier)
   - esg_compliance_status (Pass/Fail/Warning)
Do not wrap the JSON in markdown blocks like ```json, just return the raw JSON string.
"""

class RaviAgent(IntelligenceBaseAgent):
    def __init__(self, task_id: str, user_id: str = "system"):
        # Ravi gets the common tools + his specialized procurement tools
        super().__init__(
            name="Ravi", 
            role="supplier_intelligence", 
            system_prompt=RAVI_PROMPT, 
            user_id=user_id, 
            tools=INTELLIGENCE_TOOLS + RAVI_SPECIFIC_TOOLS
        )
        self.task_id = task_id

    async def execute_tool(self, function_name: str, arguments: dict) -> str:
        # Check Ravi's specific tools first
        if function_name == "query_supplier_database":
            return await query_supplier_database(arguments.get("material", ""))
        elif function_name == "analyze_supplier_risk":
            return await analyze_supplier_risk(arguments.get("supplier_name", ""))
        
        # Fallback to shared tools
        return await super().execute_tool(function_name, arguments)
