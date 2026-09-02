import json
import logging
import re
from datetime import datetime, timezone
from agents.base_agent import BaseAgent
from core.mongodb import mongodb_connection
from core.groq_engine import engine_manager

# Import actual python functions for network tools
from teams.network.shared_tools import calculate_distance, calculate_eoq
from tools.implementations.document import search_internal_documents, SEARCH_DOCUMENTS_TOOL

logger = logging.getLogger(__name__)

# --- COMMON TOOL SCHEMAS ---
NETWORK_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "calculate_distance",
            "description": "Calculates the exact air-line distance in kilometers between two global cities.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city1": {
                        "type": "string",
                        "description": "Origin city (e.g., 'Shanghai, China')"
                    },
                    "city2": {
                        "type": "string",
                        "description": "Destination city (e.g., 'Los Angeles, USA')"
                    }
                },
                "required": ["city1", "city2"]
            }
        }
    },
    SEARCH_DOCUMENTS_TOOL
]


# --- COMMON REASONING GUIDELINES ---
MATH_REASONING_INSTRUCTIONS = """
Strict Mathematical Reasoning:
- You are a mathematical agent. You must calculate, not guess.
- Use your tools to get exact distances, inventory metrics, or lead times.
- If you lack exact numbers, explicitly state your assumptions and compute based on those assumptions.
- Do not provide surface-level advice. Show the numbers.
"""

class NetworkBaseAgent(BaseAgent):
    """Overrides run_task to implement an autonomous Tool-Calling (ReAct) loop for Logistics & Math."""
    
    def __init__(self, name: str, role: str, system_prompt: str, user_id: str, tools: list, session_id: str = None):
        super().__init__(name=name, role=role, system_prompt=system_prompt, user_id=user_id, session_id=session_id)
        self.agent_tools = tools
        
    # Hook for child classes to execute their specific tools.
    async def execute_tool(self, function_name: str, arguments: dict) -> str:
        from core.approval_gate import gate_tool_call
        allowed = await gate_tool_call(
            session_id=self.session_id or "unknown",
            agent_name=self.name,
            tool_name=function_name,
            arguments=arguments,
        )
        if not allowed:
            return f"[BLOCKED by ArmorIQ] Tool '{function_name}' was denied. Agent must proceed without this data."

        if function_name == "calculate_distance":
            return await calculate_distance(arguments.get("city1", ""), arguments.get("city2", ""))
        elif function_name == "calculate_eoq":
            return await calculate_eoq(
                arguments.get("annual_demand", 0), 
                arguments.get("ordering_cost", 0), 
                arguments.get("holding_cost", 0)
            )
        elif function_name == "search_internal_documents":
            return str(search_internal_documents(arguments.get("query", ""), arguments.get("top_k", 3)))
        else:
            return f"Error: Tool {function_name} not found in Network Base Agent."

    async def run_task(self, task_description: str, model: str = "openai/gpt-oss-120b") -> str:
        await self.report_status("working", f"🧮 {self.name} modeling network topology and math...")
        
        messages = [
            {"role": "system", "content": self.system_prompt},
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
                        
                        # Use dynamic hook so subclasses can intercept specific tools
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
                    # Attempt to parse as JSON if it's JSON, otherwise store as string
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
                        await mongodb_connection.db["network_reports"].insert_one(report_doc)
                        logger.info(f"Saved {self.name}'s math/reasoning trail to DB.")
                    else:
                        logger.warning("MongoDB is not connected. Reasoning trail was not saved.")
                    
                    # Broadcast final result to frontend for transparency
                    await self.report_status("complete", f"✅ {self.name} finished task. \nFinal Output: \n{json.dumps(parsed_output, indent=2) if isinstance(parsed_output, dict) else parsed_output}")
                
                except Exception as db_err:
                    logger.error(f"Failed to save {self.name}'s math/reasoning trail to DB: {db_err}")

                return result

            except Exception as e:
                error_msg = str(e)
                
                if "Tool call validation failed" in error_msg or "tool_use_failed" in error_msg:
                    truncated_error = error_msg[:200] + "...(truncated)" if len(error_msg) > 200 else error_msg
                    logger.warning(f"[{self.name}] Tool hallucination detected. Auto-healing... Error: {truncated_error}")
                    messages.append({
                        "role": "user",
                        "content": f"System Error: {truncated_error}. You attempted to call an invalid tool name or format. DO NOT append '<|channel|>commentary' or any other suffix. Use the EXACT tool name provided."
                    })
                    continue
                    
                error_msg = f"Network agent failed: {error_msg}"
                logger.error(error_msg)
                await self.report_status("error", f"❌ {self.name} error: {error_msg}")
                return json.dumps({"error": error_msg})

        error_msg = "Network agent exceeded maximum iterations."
        await self.report_status("error", f"❌ {self.name} {error_msg}")
        return json.dumps({"error": error_msg})
