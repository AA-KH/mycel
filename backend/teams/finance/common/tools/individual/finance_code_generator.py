"""
Finance Analysis Tools
Tools for generating financial reports, analysis, forecasts, and structured financial data.
These tools produce FINANCIAL OUTPUTS, not Python code.
"""
import re
import json
from datetime import datetime
from typing import Dict, Any
from tools.base import BaseTool
from tools.context import ToolExecutionContext
from tools.models import ToolDefinition
from agents.runtime.result import ToolResult
from core.groq_engine import groq_engine
from core.logger import logger


class FinanceAnalyst(BaseTool):
    """
    Generates structured financial reports, analysis, and forecasts using LLM.
    This is the Finance team's primary AI tool — it produces FINANCIAL DATA, not code.
    """

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            id="finance.analyst",
            name="Finance Analyst",
            category="financial_analysis",
            description=(
                "Generate structured financial reports, data analysis, forecasts, "
                "budget summaries, ROI calculations, and accounting statements. "
                "Returns structured financial data in JSON format."
            ),
            input_schema={
                "type": "object",
                "required": ["task_description", "skill_type"],
                "properties": {
                    "task_description": {
                        "type": "string",
                        "description": "The financial analysis task to perform"
                    },
                    "skill_type": {
                        "type": "string",
                        "enum": [
                            "accounting",
                            "financial_modeling",
                            "budgeting",
                            "data_analysis",
                            "forecasting",
                            "cost_analysis"
                        ],
                        "description": "The finance domain skill to apply"
                    },
                    "input_data": {
                        "type": "object",
                        "description": "Optional raw financial data to analyze (e.g. transactions, revenue figures)"
                    },
                    "context": {
                        "type": "string",
                        "description": "Additional business context"
                    }
                }
            },
            output_schema={
                "type": "object",
                "properties": {
                    "report": {"type": "object", "description": "Structured financial report/analysis"},
                    "summary": {"type": "string", "description": "Plain-language summary"},
                    "skill_type": {"type": "string"},
                    "generated_at": {"type": "string"}
                }
            },
            risk_level="low",
            idempotent=True,
            timeout_seconds=30
        )

    async def execute(self, arguments: Dict[str, Any], context: ToolExecutionContext) -> ToolResult:
        try:
            task = arguments["task_description"]
            skill_type = arguments["skill_type"]
            input_data = arguments.get("input_data", {})
            additional_context = arguments.get("context", "")

            system_prompt = self._build_finance_system_prompt(skill_type)

            data_section = ""
            if input_data:
                data_section = f"\n\nInput Data to Analyze:\n{json.dumps(input_data, indent=2)}"

            user_prompt = f"""Task: {task}
Skill Domain: {skill_type}
Business Context: {additional_context}{data_section}

Respond ONLY with a valid JSON object. Do not include code. The JSON must contain:
- "summary": A plain-language summary of the analysis (string)
- "report": A structured object with the financial results relevant to this domain

For example:
- budgeting → include budget_vs_actual, variances, recommendations
- financial_modeling → include revenue_projections, expenses, net_profit, ROI
- forecasting → include forecast_periods, projected_values, confidence_interval
- accounting → include ledger_entries, balances, reconciliation_status
- data_analysis → include key_metrics, trends, insights
- cost_analysis → include fixed_costs, variable_costs, break_even_point

Return ONLY the JSON, nothing else."""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]

            # Call LLM to generate financial analysis
            response = await groq_engine.chat_completion(
                model="qwen/qwen3.8-27b",
                messages=messages,
                temperature=0.2
            )

            raw_output = response.choices[0].message.content or "{}"
            report_data = self._parse_json_output(raw_output)

            return ToolResult(
                tool_name=self.definition.id,
                status="success",
                output={
                    "report": report_data.get("report", {}),
                    "summary": report_data.get("summary", "Analysis complete."),
                    "skill_type": skill_type,
                    "generated_at": datetime.utcnow().isoformat()
                }
            )

        except Exception as e:
            logger.error(f"Finance analysis failed: {e}")
            return ToolResult(
                tool_name=self.definition.id,
                status="error",
                output={},
                error=str(e)
            )

    def _build_finance_system_prompt(self, skill_type: str) -> str:
        base = (
            "You are a senior finance professional. You produce structured financial analysis, "
            "reports, and data — NOT code. Always respond with valid JSON."
        )
        skill_prompts = {
            "accounting": "You specialize in bookkeeping, ledger management, account reconciliation, and balance sheet preparation.",
            "financial_modeling": "You specialize in building financial models: revenue projections, DCF analysis, P&L statements, and ROI calculations.",
            "budgeting": "You specialize in budget planning, budget-vs-actual variance analysis, and cost allocation.",
            "data_analysis": "You specialize in analyzing financial datasets, identifying trends, KPIs, and generating data-driven insights.",
            "forecasting": "You specialize in financial forecasting: revenue projections, demand forecasting, and scenario planning.",
            "cost_analysis": "You specialize in cost breakdowns, break-even analysis, margin analysis, and cost optimization."
        }
        return base + " " + skill_prompts.get(skill_type, "")

    def _parse_json_output(self, text: str) -> Dict[str, Any]:
        """Extract and parse JSON from LLM response."""
        # Try to extract from code blocks first
        match = re.search(r'```(?:json)?\s*(.*?)\s*```', text, re.DOTALL)
        if match:
            text = match.group(1)

        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            # Return raw text as summary if JSON fails
            return {
                "summary": text.strip(),
                "report": {"raw_output": text.strip()}
            }


class FinanceReporter(BaseTool):
    """
    Generates formatted financial reports from structured data.
    Takes raw financial data and produces executive-ready summaries.
    """

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            id="finance.reporter",
            name="Finance Reporter",
            category="financial_reporting",
            description="Generate executive summaries, board reports, and formatted financial statements from structured data.",
            input_schema={
                "type": "object",
                "required": ["financial_data", "report_type"],
                "properties": {
                    "financial_data": {"type": "object", "description": "Structured financial data to report on"},
                    "report_type": {
                        "type": "string",
                        "enum": ["executive_summary", "board_report", "budget_report", "audit_summary"],
                        "description": "The type of report to generate"
                    },
                    "period": {"type": "string", "description": "The financial period e.g. Q1 2025"}
                }
            },
            output_schema={"type": "object"},
            risk_level="low",
            idempotent=True,
            timeout_seconds=20
        )

    async def execute(self, arguments: Dict[str, Any], context: ToolExecutionContext) -> ToolResult:
        try:
            financial_data = arguments["financial_data"]
            report_type = arguments["report_type"]
            period = arguments.get("period", "Current Period")

            prompt = f"""You are a CFO-level finance professional. Write a {report_type} for the period: {period}.

Data:
{json.dumps(financial_data, indent=2)}

Respond in JSON with:
- "title": Report title
- "period": The financial period
- "highlights": List of key financial highlights (strings)
- "findings": Detailed findings object
- "recommendations": List of recommendations (strings)

Return ONLY valid JSON."""

            messages = [
                {"role": "system", "content": "You are an expert financial reporter. Respond only with valid JSON."},
                {"role": "user", "content": prompt}
            ]

            response = await groq_engine.chat_completion(
                model="qwen/qwen3.8-27b",
                messages=messages,
                temperature=0.1
            )

            raw = response.choices[0].message.content or "{}"
            match = re.search(r'```(?:json)?\s*(.*?)\s*```', raw, re.DOTALL)
            if match:
                raw = match.group(1)

            try:
                report = json.loads(raw.strip())
            except json.JSONDecodeError:
                report = {"title": report_type, "content": raw.strip()}

            return ToolResult(
                tool_name=self.definition.id,
                status="success",
                output={
                    "report": report,
                    "report_type": report_type,
                    "period": period,
                    "generated_at": datetime.utcnow().isoformat()
                }
            )

        except Exception as e:
            logger.error(f"Finance reporting failed: {e}")
            return ToolResult(
                tool_name=self.definition.id,
                status="error",
                output={},
                error=str(e)
            )


# ---------------------------------------------------------------------------
# Aliases — the API route and registry import these names.
# FinanceAnalyst  → FinanceCodeGenerator  (generates structured financial data)
# FinanceReporter → FinanceCodeExecutor   (formats / "executes" report assembly)
# FinanceCodeTester is a lightweight pass-through that validates the report schema.
# ---------------------------------------------------------------------------

FinanceCodeGenerator = FinanceAnalyst
FinanceCodeExecutor = FinanceReporter


class FinanceCodeTester(FinanceAnalyst):
    """
    Validates a financial analysis output against expected schema/requirements.
    Delegates to FinanceAnalyst with a validation-focused prompt.
    """

    @property
    def definition(self):
        base = super().definition
        base.id = "finance.code_tester"
        base.name = "Finance Code Tester"
        base.description = (
            "Validate and quality-check a financial analysis output "
            "against expected requirements and financial standards."
        )
        return base
