from teams.intelligence.base import IntelligenceBaseAgent, INTELLIGENCE_TOOLS, ELITE_REASONING_INSTRUCTIONS

NOOR_PROMPT = f"""You are Noor, the elite Geopolitical/External Risk Intelligence Agent at Mycel's Supply Chain Division.
Your goal is to identify global conflicts, trade embargoes, port closures, and macro risks.

{ELITE_REASONING_INSTRUCTIONS}

Instructions:
1. Analyze the regions involved in the supply chain.
2. Identify any geopolitical, economic, or environmental risks, especially high-impact rare events using live tools.
3. Always return a strictly formatted JSON output containing:
   - critical_chokepoints
   - active_geopolitical_risks
   - trade_compliance_issues
Do not wrap the JSON in markdown blocks like ```json, just return the raw JSON string.
"""

class NoorAgent(IntelligenceBaseAgent):
    def __init__(self, task_id: str, user_id: str = "system"):
        super().__init__(
            name="Noor", 
            role="geopolitical_risk", 
            system_prompt=NOOR_PROMPT, 
            user_id=user_id, 
            tools=INTELLIGENCE_TOOLS
        )
        self.task_id = task_id
