import json
import logging
import re
from datetime import datetime, timezone
from agents.base_agent import BaseAgent
from core.mongodb import mongodb_connection
from core.groq_engine import engine_manager

# Import the actual python functions for the base tools
from teams.intelligence.shared_tools import web_search, web_scrape

logger = logging.getLogger(__name__)

# --- COMMON TOOL SCHEMAS ---
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
                        "description": "The search query"
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

class IntelligenceBaseAgent(BaseAgent):
    """Overrides run_task to implement an autonomous Tool-Calling (ReAct) loop."""
    
    def __init__(self, name: str, role: str, system_prompt: str, user_id: str, tools: list):
        super().__init__(name=name, role=role, system_prompt=system_prompt, user_id=user_id)
        self.agent_tools = tools
        
    # Hook for child classes to execute their specific tools.
    async def execute_tool(self, function_name: str, arguments: dict) -> str:
        if function_name == "web_search":
            return await web_search(arguments.get("query", ""))
        elif function_name == "web_scrape":
            return await web_scrape(arguments.get("url", ""))
        else:
            return f"Error: Tool {function_name} not found in base agent."

    async def run_task(self, task_description: str, model: str = "openai/gpt-oss-120b") -> str:
        await self.report_status("working", f"🧠 {self.name} analyzing task and formulating research plan...")
        
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
                        
                        await self.report_status("working", f"🔍 {self.name} using tool: {function_name}({arguments})")
                        
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
                        await mongodb_connection.db["intelligence_reports"].insert_one(report_doc)
                        logger.info(f"Saved {self.name}'s reasoning trail to DB.")
                    else:
                        logger.warning("MongoDB is not connected. Reasoning trail was not saved.")
                except Exception as db_err:
                    logger.error(f"Failed to save {self.name}'s reasoning trail to DB: {db_err}")

                await self.report_status("complete", f"✅ {self.name} completed research and generated output.")
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
                    
                error_msg = f"Intelligence agent failed: {error_msg}"
                logger.error(error_msg)
                await self.report_status("error", f"❌ {self.name} error: {error_msg}")
                return json.dumps({"error": error_msg})

        error_msg = "Intelligence agent exceeded maximum iterations."
        await self.report_status("error", f"❌ {self.name} {error_msg}")
        return json.dumps({"error": error_msg})
