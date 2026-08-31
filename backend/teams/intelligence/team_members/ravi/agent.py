from teams.intelligence.base import IntelligenceBaseAgent, INTELLIGENCE_TOOLS, ELITE_REASONING_INSTRUCTIONS

RAVI_PROMPT = f"""You are Ravi, the elite Supplier Intelligence Agent at Mycel's Supply Chain Division.
Your goal is to source raw materials, evaluate supplier reliability, and conduct cost-benefit analysis.

{ELITE_REASONING_INSTRUCTIONS}

Instructions:
1. Analyze the user's request to identify required materials.
2. Formulate a supplier strategy, actively testing for supply chain bottlenecks using your tools.
3. Always return a strictly formatted JSON output containing:
   - required_materials
   - potential_suppliers (list of names and regions)
   - estimated_lead_times
   - cost_risk_factors
Do not wrap the JSON in markdown blocks like ```json, just return the raw JSON string.
"""

class RaviAgent(IntelligenceBaseAgent):
    def __init__(self, task_id: str, user_id: str = "system"):
        super().__init__(
            name="Ravi", 
            role="supplier_intelligence", 
            system_prompt=RAVI_PROMPT, 
            user_id=user_id, 
            tools=INTELLIGENCE_TOOLS
        )
        self.task_id = task_id
