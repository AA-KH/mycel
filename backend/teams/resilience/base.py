import json
import logging
import re
from datetime import datetime, timezone
from agents.base_agent import BaseAgent
from core.mongodb import mongodb_connection
from core.groq_engine import engine_manager

from teams.resilience.shared_tools import RESILIENCE_SHARED_TOOLS, calculate_financial_impact, search_alternate_suppliers, estimate_emergency_freight

logger = logging.getLogger(__name__)

RESILIENCE_REASONING_INSTRUCTIONS = """
You are a member of the Resilience Team. You must think in terms of Worst-Case Scenarios and Business Continuity.
1. ALWAYS prioritize mitigating CRITICAL risks over saving minor costs. 
2. Use the `calculate_financial_impact` tool to quantify the cost of doing nothing. If a disruption costs $500,000 in lost revenue, spending $100,000 on an emergency air charter is a mathematically sound decision.
3. Be pessimistic. Assume the disruption will happen and plan the backup route immediately.
4. If you lack exact data, state your assumptions and calculate based on them. Do not provide vague advice; provide a concrete, costed action plan.

CRITICAL JSON TOOL CALLING RULE:
NEVER append `<|channel|>commentary` or any other suffix to tool names. When calling a tool, use EXACTLY the tool name provided (e.g., `calculate_financial_impact`). Do not add commentary channels to tool calls.
"""

class ResilienceBaseAgent(BaseAgent):
    """Overrides run_task to implement an autonomous Tool-Calling (ReAct) loop for Risk & Continuity."""
    
    def __init__(self, name: str, role: str, system_prompt: str, user_id: str, tools: list):
        super().__init__(name=name, role=role, system_prompt=system_prompt, user_id=user_id)
        # Combine specific tools with Resilience shared tools
        self.agent_tools = tools + RESILIENCE_SHARED_TOOLS
        
    async def execute_tool(self, function_name: str, arguments: dict) -> str:
        """Shared tool execution hook for Resilience Agents."""
        if function_name == "calculate_financial_impact":
            return await calculate_financial_impact(
                arguments.get("downtime_days", 0),
                arguments.get("daily_revenue_loss", 0.0),
                arguments.get("fixed_costs_per_day", 0.0)
            )
        elif function_name == "search_alternate_suppliers":
            return await search_alternate_suppliers(
                arguments.get("product_category", ""),
                arguments.get("avoid_region", "")
            )
        elif function_name == "estimate_emergency_freight":
            return await estimate_emergency_freight(
                arguments.get("weight_kg", 0.0),
                arguments.get("mode", "")
            )
        else:
            return f"Error: Tool {function_name} not found in Resilience Base Agent."

    async def run_task(self, task_description: str, model: str = "openai/gpt-oss-120b") -> str:
        await self.report_status("working", f"🛡️ {self.name} analyzing resilience and continuity...")
        
        # Combine role prompt with resilience reasoning rules
        full_system_prompt = f"{self.system_prompt}\n\n{RESILIENCE_REASONING_INSTRUCTIONS}"
        
        messages = [
            {"role": "system", "content": full_system_prompt},
            {"role": "user", "content": task_description}
        ]
        
        MAX_ITERATIONS = 15
        iteration = 0
        
        while iteration < MAX_ITERATIONS:
            iteration += 1
            
            try:
                if len(messages) > 8:
                    messages = [messages[0]] + messages[-6:]

                kwargs = {
                    "model": model,
                    "messages": messages,
                    "team_id": self.name.lower(),
                    "temperature": 0.1
                }
                
                if self.agent_tools:
                    kwargs["tools"] = self.agent_tools
                    kwargs["tool_choice"] = "auto"

                response = await engine_manager.chat_completion(**kwargs)
                
                response_message = response.choices[0].message
                
                if response_message.tool_calls:
                    assistant_msg = response_message.model_dump(exclude_unset=True)
                    if assistant_msg.get("content") and isinstance(assistant_msg["content"], str):
                        assistant_msg["content"] = re.sub(r'<think>.*?</think>', '', assistant_msg["content"], flags=re.DOTALL).strip()
                        if not assistant_msg["content"]:
                            assistant_msg.pop("content", None)
                    messages.append(assistant_msg)
                    
                    for tool_call in response_message.tool_calls:
                        function_name = tool_call.function.name
                        arguments = json.loads(tool_call.function.arguments)
                        
                        await self.report_status("working", f"⚙️ {self.name} calculating: {function_name}({arguments})")
                        
                        tool_result = await self.execute_tool(function_name, arguments)
                            
                        messages.append({
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": function_name,
                            "content": tool_result,
                        })
                    
                    continue
                
                raw_result = response_message.content or ""
                result = re.sub(r'<think>.*?</think>', '', raw_result, flags=re.DOTALL).strip()
                
                if result.startswith("```json"):
                    result = result.replace("```json", "", 1).strip()
                if result.endswith("```"):
                    result = result[:-3].strip()
                    
                # Save the complete reasoning trail (messages) and final output to MongoDB for Chatbot explainability
                try:
                    try:
                        parsed_output = json.loads(result)
                    except json.JSONDecodeError:
                        parsed_output = result
                        
                    report_doc = {
                        "agent_name": self.name,
                        "role": self.role,
                        "task_description": task_description,
                        "reasoning_trail": messages,
                        "final_output": parsed_output,
                        "timestamp": datetime.now(timezone.utc)
                    }
                    if mongodb_connection.client is not None:
                        await mongodb_connection.db["resilience_reports"].insert_one(report_doc)
                        logger.info(f"Saved {self.name}'s resilience trail to DB.")
                    else:
                        logger.warning("MongoDB is not connected. Reasoning trail was not saved.")
                    
                    # Broadcast final result to frontend for transparency
                    await self.report_status("complete", f"✅ {self.name} finished task. \nFinal Output: \n{json.dumps(parsed_output, indent=2) if isinstance(parsed_output, dict) else parsed_output}")
                
                except Exception as db_err:
                    logger.error(f"Failed to save {self.name}'s resilience trail to DB: {db_err}")

                return result

            except Exception as e:
                error_msg = str(e)
                
                if "Tool call validation failed" in error_msg or "tool_use_failed" in error_msg:
                    logger.warning(f"[{self.name}] Tool hallucination detected. Auto-healing... Error: {error_msg}")
                    messages.append({
                        "role": "user",
                        "content": f"System Error: {error_msg}. You attempted to call an invalid tool name or format. DO NOT append '<|channel|>commentary' or any other suffix. Use the EXACT tool name provided."
                    })
                    continue
                    
                error_msg = f"Resilience agent failed: {error_msg}"
                logger.error(error_msg)
                await self.report_status("error", f"❌ {self.name} error: {error_msg}")
                return json.dumps({"error": error_msg})
                
        error_msg = "Resilience agent exceeded maximum iterations."
        await self.report_status("error", f"❌ {self.name} {error_msg}")
        return json.dumps({"error": error_msg})
