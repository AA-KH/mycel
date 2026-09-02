import json
import re
from datetime import datetime, timezone
from typing import Dict, Any, List

from core.logger import logger
from agents.base_agent import BaseAgent
from core.mongodb import mongodb_connection
from core.groq_engine import engine_manager


class ArchitectureBaseAgent(BaseAgent):
    """
    Base agent class for the Architecture Team.
    Provides standard orchestration, memory handling, tool execution,
    and MongoDB persistence for architectural decisions and outputs.
    """

    def __init__(self, name: str, role: str, system_prompt: str, agent_tools: list = None, session_id: str = None):
        super().__init__(name=name, role=role, system_prompt=system_prompt, session_id=session_id)
        from tools.implementations.document import SEARCH_DOCUMENTS_TOOL
        self.agent_tools = agent_tools or []
        if SEARCH_DOCUMENTS_TOOL not in self.agent_tools:
            self.agent_tools.append(SEARCH_DOCUMENTS_TOOL)

    async def report_status(self, state: str, summary: str, event_type: str = "status_update", break_activity: str | None = None):
        """Override BaseAgent.report_status to also publish events to project_events for the timeline."""
        await super().report_status(state, summary, event_type, break_activity)
        from core.events import event_publisher
        await event_publisher.publish(
            self.session_id, 
            "log", 
            {"level": "info" if state in ["working", "complete"] else "error", "text": summary}
        )

    async def execute_tool(self, function_name: str, arguments: dict) -> Any:
        """
        Executes shared architecture tools.
        Child classes can override this to implement member-specific tools.
        """
        from .shared_tools import generate_mermaid_graph, validate_json_schema
        from core.approval_gate import gate_tool_call

        allowed = await gate_tool_call(
            session_id=self.session_id or "unknown",
            agent_name=self.name,
            tool_name=function_name,
            arguments=arguments,
        )
        if not allowed:
            return f"[BLOCKED by ArmorIQ] Tool '{function_name}' was denied. Agent must proceed without this data."

        if function_name == "generate_mermaid_graph":
            return await generate_mermaid_graph(
                mermaid_syntax=arguments.get("mermaid_syntax", ""),
                title=arguments.get("title", "Architecture Diagram")
            )
        elif function_name == "validate_json_schema":
            return await validate_json_schema(
                arguments.get("schema", {}),
                arguments.get("sample_data", {})
            )
        elif function_name == "search_internal_documents":
            from tools.implementations.document import search_internal_documents
            return str(search_internal_documents(arguments.get("query", ""), arguments.get("top_k", 3)))
        else:
            return f"Error: Tool '{function_name}' not recognized by ArchitectureBaseAgent."

    async def run_task(self, task_description: str, model: str = "qwen/qwen3.8-27b") -> str:
        await self.report_status("working", f"📐 {self.name} beginning architectural analysis...")

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": task_description}
        ]

        MAX_ITERATIONS = 15
        iteration = 0

        while iteration < MAX_ITERATIONS:
            iteration += 1
            try:
                # ── Message Truncation (Anti-413 Payload Too Large) ──
                if len(messages) > 8:
                    # Keep system (0) and user query (1), then the last 5 messages
                    messages = [messages[0], messages[1]] + messages[-5:]

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

                        await self.report_status(
                            "working",
                            f"📐 {self.name} utilizing: {function_name}()"
                        )
                        tool_result = await self.execute_tool(function_name, arguments)
                        messages.append({
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": function_name,
                            "content": str(tool_result),
                        })
                    continue

                raw_result = response_message.content or ""
                result = re.sub(r'<think>.*?</think>', '', raw_result, flags=re.DOTALL).strip()
                if result.startswith("```json"):
                    result = result.replace("```json", "", 1).strip()
                if result.endswith("```"):
                    result = result[:-3].strip()

                # Save to MongoDB
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
                        await mongodb_connection.db["architecture_reports"].insert_one(report_doc)
                        logger.info(f"Saved {self.name}'s architecture design to DB (architecture_reports).")
                    else:
                        logger.warning("MongoDB not connected. Architecture trail not saved.")

                    await self.report_status(
                        "complete",
                        f"✅ {self.name} finalized design.\nOutput:\n{json.dumps(parsed_output, indent=2) if isinstance(parsed_output, dict) else parsed_output}"
                    )
                except Exception as db_err:
                    logger.error(f"Failed to save {self.name}'s architecture report: {db_err}")

                return result

            except Exception as e:
                error_msg = str(e)
                
                # Auto-Healing for Tool Hallucinations / Validation Errors
                if "Tool call validation failed" in error_msg or "tool_use_failed" in error_msg:
                    truncated_error = error_msg[:200] + "...(truncated)" if len(error_msg) > 200 else error_msg
                    logger.warning(f"[{self.name}] Tool hallucination detected. Auto-healing... Error: {truncated_error}")
                    messages.append({
                        "role": "user",
                        "content": f"System Error: {truncated_error}. You attempted to call an invalid tool name or format. DO NOT append '<|channel|>commentary' or any other suffix. Use the EXACT tool name provided."
                    })
                    continue
                    
                error_msg = f"Architecture agent failed: {error_msg}"
                logger.error(error_msg)
                await self.report_status("error", f"❌ {self.name} error: {error_msg}")
                return json.dumps({"error": error_msg})

        error_msg = "Architecture agent exceeded maximum iterations."
        await self.report_status("error", f"❌ {self.name} {error_msg}")
        return json.dumps({"error": error_msg})
