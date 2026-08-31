import json
import logging
import re
from agents.base_agent import BaseAgent
from core.groq_engine import groq_engine
from teams.intelligence.tools import web_search, web_scrape

logger = logging.getLogger(__name__)

# --- TOOL SCHEMAS ---
INTELLIGENCE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Performs a live web search. Use this for discovering real-time market data, geopolitical news, or supplier info.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query (e.g. 'lithium battery shortage 2026')"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_scrape",
            "description": "Scrapes a specific URL and returns the clean text content. Use this to read a full article or report.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to scrape"
                    }
                },
                "required": ["url"]
            }
        }
    }
]

# --- COMMON REASONING GUIDELINES ---
ELITE_REASONING_INSTRUCTIONS = """
Elite Reasoning & Extreme Case Validation:
- You must use deep Chain of Thought reasoning. Do not accept surface-level data.
- Think about extreme edge cases (Black Swan events). What if the primary data source is wrong? What if the market shifts overnight?
- Cross-validate your findings using your tools. If a supplier looks good, actively search for negative news or lawsuits to test extreme worst-case scenarios.
"""

# --- SYSTEM PROMPTS ---

MIRA_PROMPT = f"""You are Mira, the elite Market & Demand Intelligence Agent at Mycel's Supply Chain Division.
Your goal is to gather and analyze consumer demand, market trends, and product viability.
{ELITE_REASONING_INSTRUCTIONS}
Instructions:
1. Analyze the user's request.
2. Use your tools to fetch live market data.
3. Always return a strictly formatted JSON output containing:
   - target_demographics
   - key_competitors
   - expected_demand_volume
   - market_trends
Do not wrap the JSON in markdown blocks like ```json, just return the raw JSON string.
"""

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

# --- BASE TOOL AGENT ---
class IntelligenceBaseAgent(BaseAgent):
    """Overrides run_task to implement an autonomous Tool-Calling (ReAct) loop."""
    
    async def run_task(self, task_description: str, model: str = "llama-3.3-70b-versatile") -> str:
        await self.report_status("working", f"🧠 {self.name} analyzing task and formulating research plan...")
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": task_description}
        ]
        
        # Prevent infinite loops
        MAX_ITERATIONS = 5
        iteration = 0
        
        while iteration < MAX_ITERATIONS:
            iteration += 1
            
            try:
                response = await groq_engine.chat_completion(
                    model=model,
                    messages=messages,
                    tools=INTELLIGENCE_TOOLS,
                    tool_choice="auto",
                    temperature=0.3
                )
                
                response_message = response.choices[0].message
                
                # If LLM wants to call a tool
                if response_message.tool_calls:
                    # Append assistant's request to call tools
                    # We must convert it to a dict format that Groq expects in history
                    messages.append(response_message.model_dump(exclude_unset=True))
                    
                    for tool_call in response_message.tool_calls:
                        function_name = tool_call.function.name
                        arguments = json.loads(tool_call.function.arguments)
                        
                        await self.report_status("working", f"🔍 {self.name} using tool: {function_name}({arguments})")
                        
                        # Execute the actual Python tool
                        if function_name == "web_search":
                            tool_result = await web_search(arguments.get("query", ""))
                        elif function_name == "web_scrape":
                            tool_result = await web_scrape(arguments.get("url", ""))
                        else:
                            tool_result = f"Error: Tool {function_name} not found."
                            
                        # Append the tool result
                        messages.append({
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": function_name,
                            "content": tool_result,
                        })
                    
                    # Loop continues, LLM will read the tool results
                    continue
                
                # If no tool calls, the LLM has generated the final output
                raw_result = response_message.content or ""
                # Strip out any <think> tags if Qwen model is used
                result = re.sub(r'<think>.*?</think>', '', raw_result, flags=re.DOTALL).strip()
                
                # Strip markdown blocks if the LLM hallucinated them
                if result.startswith("```json"):
                    result = result.replace("```json", "", 1).strip()
                if result.endswith("```"):
                    result = result[:-3].strip()
                    
                await self.report_status("complete", f"✅ {self.name} completed research and generated output.")
                return result

            except Exception as e:
                logger.error(f"{self.name} Agent Error in iteration {iteration}: {e}")
                await self.report_status("failure", f"❌ {self.name} encountered an error: {str(e)[:60]}")
                # Fallback return so the whole pipeline doesn't crash
                return f'{{"error": "Agent failed during execution: {str(e)}"}}'
                
        return '{"error": "Max tool iterations reached without final output."}'


# --- AGENT CLASSES ---

class MiraAgent(IntelligenceBaseAgent):
    def __init__(self, task_id: str, user_id: str = "system"):
        super().__init__(name="Mira", role="market_intelligence", system_prompt=MIRA_PROMPT, user_id=user_id)
        self.task_id = task_id

class RaviAgent(IntelligenceBaseAgent):
    def __init__(self, task_id: str, user_id: str = "system"):
        super().__init__(name="Ravi", role="supplier_intelligence", system_prompt=RAVI_PROMPT, user_id=user_id)
        self.task_id = task_id

class AnikaAgent(IntelligenceBaseAgent):
    def __init__(self, task_id: str, user_id: str = "system"):
        super().__init__(name="Anika", role="industry_benchmarking", system_prompt=ANIKA_PROMPT, user_id=user_id)
        self.task_id = task_id

class NoorAgent(IntelligenceBaseAgent):
    def __init__(self, task_id: str, user_id: str = "system"):
        super().__init__(name="Noor", role="geopolitical_risk", system_prompt=NOOR_PROMPT, user_id=user_id)
        self.task_id = task_id
