import json
import logging
import re
from datetime import datetime, timezone
from agents.base_agent import BaseAgent
from core.mongodb import mongodb_connection
from core.groq_engine import engine_manager

from teams.council.shared_tools import (
    score_vendor_contract_risk,
    check_esg_compliance,
    check_trade_policy,
    analyze_strategic_cost_benefit
)

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# SHARED TOOL SCHEMAS (available to all Council members)
# ─────────────────────────────────────────────────────────────
COUNCIL_SHARED_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "score_vendor_contract_risk",
            "description": "Scores a vendor contract from 0-100 risk using concentration, geopolitical exposure, value, and duration. Use this before approving any vendor contract.",
            "parameters": {
                "type": "object",
                "properties": {
                    "vendor_name": {"type": "string", "description": "Name of the vendor."},
                    "contract_value_usd": {"type": "number", "description": "Total contract value in USD."},
                    "contract_duration_months": {"type": "integer", "description": "Contract duration in months."},
                    "single_source": {"type": "boolean", "description": "True if this is the only supplier for this product."},
                    "country": {"type": "string", "description": "Country where the vendor is based."}
                },
                "required": ["vendor_name", "contract_value_usd", "contract_duration_months", "single_source", "country"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_esg_compliance",
            "description": "Checks a vendor's ESG compliance posture: ISO 14001, SA8000, ESG reporting, and carbon footprint. Flags regulatory gaps.",
            "parameters": {
                "type": "object",
                "properties": {
                    "vendor_name": {"type": "string"},
                    "country": {"type": "string"},
                    "industry": {"type": "string"},
                    "has_iso_14001": {"type": "boolean", "description": "Does the vendor hold ISO 14001 certification?"},
                    "has_sa8000": {"type": "boolean", "description": "Does the vendor hold SA8000 Social Accountability certification?"},
                    "has_annual_esg_report": {"type": "boolean", "description": "Does the vendor publish an annual ESG report?"},
                    "carbon_footprint_tons_per_year": {"type": "number", "description": "Vendor's annual carbon footprint in metric tons."}
                },
                "required": ["vendor_name", "country", "industry", "has_iso_14001", "has_sa8000", "has_annual_esg_report", "carbon_footprint_tons_per_year"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_trade_policy",
            "description": "Checks active trade restrictions, tariffs, and embargo status between two countries for a given product category.",
            "parameters": {
                "type": "object",
                "properties": {
                    "origin_country": {"type": "string", "description": "Country where goods originate."},
                    "destination_country": {"type": "string", "description": "Country where goods are being shipped to."},
                    "product_category": {"type": "string", "description": "Type of product (e.g., 'Electronics', 'Steel', 'Pharmaceuticals')."}
                },
                "required": ["origin_country", "destination_country", "product_category"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_strategic_cost_benefit",
            "description": "Computes NPV, ROI, and payback period for a strategic business initiative. Use this to justify or reject major spending proposals to the Council.",
            "parameters": {
                "type": "object",
                "properties": {
                    "initiative_name": {"type": "string"},
                    "upfront_investment_usd": {"type": "number", "description": "Total upfront cost."},
                    "annual_savings_usd": {"type": "number", "description": "Annual cost savings from the initiative."},
                    "risk_mitigation_value_usd": {"type": "number", "description": "Annual monetary value of risk avoided."},
                    "implementation_years": {"type": "integer", "description": "Number of years to evaluate."}
                },
                "required": ["initiative_name", "upfront_investment_usd", "annual_savings_usd", "risk_mitigation_value_usd", "implementation_years"]
            }
        }
    }
]

# ─────────────────────────────────────────────────────────────
# COUNCIL REASONING STANDARD
# ─────────────────────────────────────────────────────────────
COUNCIL_REASONING_INSTRUCTIONS = """
You are a member of the Mycel Council — the strategic governing body.

COUNCIL MANDATE:
1. ALWAYS use your tools BEFORE forming an opinion. Gut-feel decisions are forbidden.
2. Every recommendation must cite a specific number, score, or calculation.
3. Think in terms of 3-5 year strategic consequences, not just immediate costs.
4. If a risk score is HIGH (≥70), you MUST escalate it and recommend a mitigation path.
5. ESG compliance and trade policy are non-negotiable. Never approve a vendor that fails these checks.
6. Your final output must be a binding Council Resolution in this JSON format:

```json
{
  "resolution_id": "COUNCIL-RES-XXXX",
  "proposed_by": "<Your Name>",
  "subject": "<Topic>",
  "analysis_summary": "<What the data showed>",
  "risks_identified": ["<risk1>", "<risk2>"],
  "council_decision": "APPROVED / REJECTED / DEFERRED",
  "conditions": ["<condition1 if approved with caveats>"],
  "next_review_date": "<YYYY-MM-DD>"
}
```
"""


# ─────────────────────────────────────────────────────────────
# BASE AGENT CLASS
# ─────────────────────────────────────────────────────────────
class CouncilBaseAgent(BaseAgent):
    """
    Base agent for all 5 Council members.
    Implements the tool-calling (ReAct) loop and saves full reasoning
    trails to MongoDB (council_reports collection) for XAI / Chatbot KB.
    """

    def __init__(self, name: str, role: str, system_prompt: str, user_id: str, tools: list):
        super().__init__(name=name, role=role, system_prompt=system_prompt, user_id=user_id)
        # Each member's specific tools + shared Council tools
        self.agent_tools = tools + COUNCIL_SHARED_TOOLS

    async def execute_tool(self, function_name: str, arguments: dict) -> str:
        """Shared Council tool execution — delegates shared tools here."""
        if function_name == "score_vendor_contract_risk":
            return await score_vendor_contract_risk(
                arguments.get("vendor_name", ""),
                arguments.get("contract_value_usd", 0.0),
                arguments.get("contract_duration_months", 12),
                arguments.get("single_source", False),
                arguments.get("country", "")
            )
        elif function_name == "check_esg_compliance":
            return await check_esg_compliance(
                arguments.get("vendor_name", ""),
                arguments.get("country", ""),
                arguments.get("industry", ""),
                arguments.get("has_iso_14001", False),
                arguments.get("has_sa8000", False),
                arguments.get("has_annual_esg_report", False),
                arguments.get("carbon_footprint_tons_per_year", 0.0)
            )
        elif function_name == "check_trade_policy":
            return await check_trade_policy(
                arguments.get("origin_country", ""),
                arguments.get("destination_country", ""),
                arguments.get("product_category", "")
            )
        elif function_name == "analyze_strategic_cost_benefit":
            return await analyze_strategic_cost_benefit(
                arguments.get("initiative_name", ""),
                arguments.get("upfront_investment_usd", 0.0),
                arguments.get("annual_savings_usd", 0.0),
                arguments.get("risk_mitigation_value_usd", 0.0),
                arguments.get("implementation_years", 3)
            )
        else:
            return f"Error: Tool '{function_name}' not found in CouncilBaseAgent."

    async def run_task(self, task_description: str, model: str = "openai/gpt-oss-120b") -> str:
        await self.report_status("working", f"🏛️ {self.name} convening Council analysis...")

        full_system_prompt = f"{self.system_prompt}\n\n{COUNCIL_REASONING_INSTRUCTIONS}"
        messages = [
            {"role": "system", "content": full_system_prompt},
            {"role": "user", "content": task_description}
        ]

        MAX_ITERATIONS = 15
        iteration = 0

        while iteration < MAX_ITERATIONS:
            iteration += 1
            try:
                response = await engine_manager.chat_completion(
                    model=model,
                    messages=messages,
                    team_id=self.name.lower(),
                    tools=self.agent_tools,
                    tool_choice="auto",
                    temperature=0.1
                )

                response_message = response.choices[0].message

                if response_message.tool_calls:
                    messages.append(response_message.model_dump(exclude_unset=True))
                    for tool_call in response_message.tool_calls:
                        function_name = tool_call.function.name
                        arguments = json.loads(tool_call.function.arguments)

                        await self.report_status(
                            "working",
                            f"⚖️ {self.name} evaluating: {function_name}({list(arguments.keys())})"
                        )
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

                # ── Save to MongoDB as XAI Knowledge Base ──
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
                        await mongodb_connection.db["council_reports"].insert_one(report_doc)
                        logger.info(f"Saved {self.name}'s Council resolution to DB (council_reports).")
                    else:
                        logger.warning("MongoDB not connected. Council reasoning trail not saved.")

                    await self.report_status(
                        "complete",
                        f"✅ {self.name} issued resolution.\nOutput:\n{json.dumps(parsed_output, indent=2) if isinstance(parsed_output, dict) else parsed_output}"
                    )
                except Exception as db_err:
                    logger.error(f"Failed to save {self.name}'s Council resolution: {db_err}")

                return result

            except Exception as e:
                error_msg = f"Council agent failed: {str(e)}"
                logger.error(error_msg)
                await self.report_status("error", f"❌ {self.name} error: {error_msg}")
                return json.dumps({"error": error_msg})

        error_msg = "Council agent exceeded maximum iterations."
        await self.report_status("error", f"❌ {self.name} {error_msg}")
        return json.dumps({"error": error_msg})
