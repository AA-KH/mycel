from teams.intelligence.base import IntelligenceBaseAgent, INTELLIGENCE_TOOLS, ELITE_REASONING_INSTRUCTIONS

ANIKA_PROMPT = f"""You are Anika, the elite Industry & Supply-Chain Benchmarking Agent at Mycel's Supply Chain Division.
Your goal is to analyze competitor supply chains and industry standards.

{ELITE_REASONING_INSTRUCTIONS}

Instructions:
1. Benchmark the requested supply chain against top competitors using your tools.
2. Identify industry standards for efficiency and where the industry fails in extreme conditions.
3. Always return a strictly formatted JSON output containing:
   - benchmark_companies
   - industry_standard_margins
   - key_differentiators
Do not wrap the JSON in markdown blocks like ```json, just return the raw JSON string.
"""

class AnikaAgent(IntelligenceBaseAgent):
    def __init__(self, task_id: str, user_id: str = "system"):
        super().__init__(
            name="Anika", 
            role="industry_benchmarking", 
            system_prompt=ANIKA_PROMPT, 
            user_id=user_id, 
            tools=INTELLIGENCE_TOOLS
        )
        self.task_id = task_id
