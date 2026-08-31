"""
Finance Developer Agent
An agent specialized in developing, testing, and executing finance-related Python code.
"""
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from core import groq_engine

from agents.runtime.result import ToolRequest, ToolResult
from tools.gateway import CoreToolGateway

logger = logging.getLogger(__name__)


class FinanceDeveloperAgent:
    """
    AI Agent for the Finance Development team.
    Uses domain-specific finance tools to:
    - Generate Python code for financial tasks
    - Execute and test that code
    - Refine existing code based on feedback
    """

    def __init__(self, employee_id: str = "emp_fin_developer_001"):
        self.employee_id = employee_id
        self.session_id = str(uuid.uuid4())
        self.tool_gateway = CoreToolGateway()

        self.finance_skills = [
            "accounting",
            "financial_modeling",
            "budgeting",
            "data_analysis",
            "forecasting",
            "cost_analysis",
        ]

        self.finance_tools = [
            "finance.code_generator",
            "finance.code_executor",
            "finance.code_tester",
            "finance.analyst",
            "finance.reporter",
            "spreadsheet.processing",
            "financial.calculator"
        ]

    async def develop_finance_solution(
        self,
        task_description: str,
        skill_type: str,
        context: str = "",
        test_requirements: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Generate, test, and (optionally) execute finance Python code for a given task.

        Args:
            task_description: Description of the finance task (e.g. 'Forecast Q4 revenue')
            skill_type: One of the supported finance skill domains
            context: Extra business context
            test_requirements: Specific test cases to include

        Returns:
            Dict with 'status', 'code', 'tests', 'execution_result', 'session_id'
        """
        logger.info(
            f"[FinanceDeveloperAgent] Developing solution | skill={skill_type} | task={task_description[:60]}"
        )

        # Step 1 — Generate code
        gen_request = ToolRequest(
            tool_name="finance.code_generator",
            employee_id=self.employee_id,
            execution_id=self.session_id,
            arguments={
                "task_description": task_description,
                "skill_type": skill_type,
                "context": context,
                "test_requirements": test_requirements or [],
            },
        )
        gen_result = await self.tool_gateway.execute(gen_request)

        if gen_result.status != "success":
            logger.error(f"[FinanceDeveloperAgent] Code generation failed: {gen_result.error}")
            return {
                "status": "error",
                "error": gen_result.error,
                "session_id": self.session_id,
            }

        generated_code = gen_result.output.get("code", "")

        # Step 2 — Generate tests
        test_request = ToolRequest(
            tool_name="finance.code_tester",
            employee_id=self.employee_id,
            execution_id=self.session_id,
            arguments={
                "code": generated_code,
                "skill_type": skill_type,
                "test_requirements": test_requirements or [],
            },
        )
        test_result = await self.tool_gateway.execute(test_request)
        tests_output = test_result.output if test_result.status == "success" else {}

        # Step 3 — Execute code
        exec_request = ToolRequest(
            tool_name="finance.code_executor",
            employee_id=self.employee_id,
            execution_id=self.session_id,
            arguments={"code": generated_code},
        )
        exec_result = await self.tool_gateway.execute(exec_request)
        execution_output = exec_result.output if exec_result.status == "success" else {
            "error": exec_result.error
        }

        logger.info(f"[FinanceDeveloperAgent] Solution complete | skill={skill_type}")
        return {
            "status": "success",
            "code": generated_code,
            "skill_type": skill_type,
            "tests": tests_output,
            "execution_result": execution_output,
            "session_id": self.session_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    async def refine_code(
        self,
        original_code: str,
        feedback: str,
        skill_type: str,
    ) -> Dict[str, Any]:
        """
        Refine existing finance code based on feedback using the LLM.

        Args:
            original_code: The Python code to improve
            feedback: Specific guidance for the refinement
            skill_type: Finance skill domain (for system-prompt context)

        Returns:
            Dict with 'status', 'code', 'changes_summary', 'session_id'
        """
        logger.info(
            f"[FinanceDeveloperAgent] Refining code | skill={skill_type} | feedback={feedback[:60]}"
        )

        system_prompt = (
            f"You are a senior finance software engineer specialising in {skill_type}. "
            "Your job is to refine Python code based on feedback. "
            "Return ONLY the improved Python code, no explanations."
        )

        user_prompt = (
            f"Refine the following Python code based on this feedback:\n\n"
            f"Feedback: {feedback}\n\n"
            f"Original Code:\n```python\n{original_code}\n```\n\n"
            "Return ONLY the improved Python code."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        try:
            response = await groq_engine.chat_completion(
                model="grok-beta",
                messages=messages,
                temperature=0.2,
            )

            refined_code = response.choices[0].message.content or original_code

            # Strip markdown code fences if present
            import re
            match = re.search(r"```(?:python)?\s*(.*?)\s*```", refined_code, re.DOTALL)
            if match:
                refined_code = match.group(1)

            return {
                "status": "success",
                "code": refined_code.strip(),
                "skill_type": skill_type,
                "feedback_applied": feedback,
                "session_id": self.session_id,
                "refined_at": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"[FinanceDeveloperAgent] Code refinement failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "session_id": self.session_id,
            }

    async def analyze(
        self,
        task_description: str,
        skill_type: str,
        input_data: Optional[Dict[str, Any]] = None,
        context: str = "",
    ) -> Dict[str, Any]:
        """
        Perform financial analysis using the finance.analyst tool.
        Kept for backward compatibility.
        """
        logger.info(
            f"[FinanceDeveloperAgent] Starting analysis | skill={skill_type} | task={task_description[:60]}"
        )

        request = ToolRequest(
            tool_name="finance.analyst",
            employee_id=self.employee_id,
            execution_id=self.session_id,
            arguments={
                "task_description": task_description,
                "skill_type": skill_type,
                "input_data": input_data or {},
                "context": context,
            },
        )
        result = await self.tool_gateway.execute(request)
        if result.status == "success":
            logger.info(f"[FinanceDeveloperAgent] Analysis complete | skill={skill_type}")
            return {
                "status": "success",
                "report": result.output.get("report", {}),
                "summary": result.output.get("summary", ""),
                "skill_type": skill_type,
                "session_id": self.session_id,
                "generated_at": result.output.get(
                    "generated_at", datetime.now(timezone.utc).isoformat()
                ),
            }
        else:
            logger.error(f"[FinanceDeveloperAgent] Analysis failed: {result.error}")
            return {
                "status": "error",
                "error": result.error,
                "session_id": self.session_id,
            }

    async def generate_report(
        self,
        financial_data: Dict[str, Any],
        report_type: str = "executive_summary",
        period: str = ""
    ) -> Dict[str, Any]:
        """Generate a formatted financial report from structured data."""
        logger.info(f"[FinanceDeveloperAgent] Generating {report_type} for {period}")
        request = ToolRequest(
            tool_name="finance.reporter",
            employee_id=self.employee_id,
            execution_id=self.session_id,
            arguments={
                "financial_data": financial_data,
                "report_type": report_type,
                "period": period or "Current Period"
            }
        )
        result = await self.tool_gateway.execute(request)
        if result.status == "success":
            return {
                "status": "success",
                "report": result.output.get("report", {}),
                "report_type": report_type,
                "period": result.output.get("period", period),
                "session_id": self.session_id
            }
        return {"status": "error", "error": result.error, "session_id": self.session_id}


# Backward-compat alias
FinanceAgent = FinanceDeveloperAgent
