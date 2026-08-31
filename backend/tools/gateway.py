from typing import Dict, Any

from agents.runtime.interfaces import ToolGateway
from agents.runtime.result import ToolRequest, ToolResult

from .registry import ToolRegistry, registry as global_registry
from .security import ToolSecurityPolicy
from .executor import ToolExecutor
from .context import ToolExecutionContext
from .models import ToolError
from workforce.employees.registry import EmployeeRegistry
from core.logger import logger


def _build_semantic_intent(
    tool_id: str, arguments: Dict[str, Any], employee_id: str, task_id: str
) -> str:
    """
    Build a semantically meaningful intent string for the Security Gateway / ArmorIQ.

    ArmorIQ should see the WHAT and WHY, not just the tool name.
    This allows policy evaluation at a meaningful level rather than raw API calls.

    Examples:
        "Creative media generation: TEXT_TO_IMAGE for social_media — emp_riya_sharma task_abc"
        "Creative media animation: IMAGE_TO_VIDEO — emp_riya_sharma task_abc"
        "Execute tool web.search — emp_riya_sharma task_abc"
    """
    operation = arguments.get("operation", "")
    purpose = arguments.get("purpose", "")
    prompt_preview = str(arguments.get("prompt", ""))[:60]

    if tool_id == "creative.media.generate":
        op = operation or "TEXT_TO_IMAGE"
        base = f"Creative media generation: {op}"
        if purpose:
            base += f" for {purpose}"
        if prompt_preview:
            base += f' — "{prompt_preview}..."'
    elif tool_id == "creative.media.transform":
        op = operation or "IMAGE_VARIATION"
        base = f"Creative media transformation: {op}"
        src = arguments.get("source_artifact_id", "")
        if src:
            base += f" of artifact {src}"
    elif tool_id == "creative.media.animate":
        op = operation or "IMAGE_TO_VIDEO"
        base = f"Creative media animation: {op}"
        src = arguments.get("source_artifact_id", "")
        duration = arguments.get("duration_seconds", 5)
        if src:
            base += f" of artifact {src} ({duration}s)"
    elif tool_id == "design.canvas":
        brief = str(arguments.get("brief", ""))[:60]
        base = f"Design canvas layout generation: \"{brief}...\""
    else:
        base = f"Execute tool {tool_id}"

    return f"{base} — {employee_id} task={task_id}"


class CoreToolGateway(ToolGateway):
    """
    The main entry point for tool execution from the AgentRuntime.
    Enforces security, validates capabilities, and executes via ToolExecutor.
    """
    def __init__(self, registry: ToolRegistry = global_registry, employee_registry: EmployeeRegistry = None):
        self.registry = registry
        # Optional injection, fallback to global if None
        self.employee_registry = employee_registry or EmployeeRegistry()

    async def execute(self, request: ToolRequest) -> ToolResult:
        try:
            # 1. Resolve Tool Definition & Implementation
            tool_id = request.tool_name
            definition = self.registry.get_definition(tool_id)
            implementation = self.registry.get_implementation(tool_id)
            
            # 2. Fetch Employee to verify allowed tools
            if request.employee_id == "sys":
                allowed_tools = [tool_id]  # System has access to everything
                company_id = "system"
            else:
                employee = await self.employee_registry.employee_repo.get_by_id(request.employee_id)
                if not employee:
                    return self._error_result(tool_id, f"Employee {request.employee_id} not found.")
                # Phase 3 definitions store tools in a list of strings
                allowed_tools = employee.tools if hasattr(employee, "tools") else []
                company_id = employee.company_id if hasattr(employee, "company_id") else "unknown"
            
            # 3. Security & Validation (Legacy)
            ToolSecurityPolicy.validate_request(request, definition, allowed_tools)
            
            # 4. Construct Tool Context
            context = ToolExecutionContext(
                request_id=f"req_{request.execution_id}_{tool_id}",
                execution_id=request.execution_id,
                task_id=request.execution_id, # Assuming task_id is closely related
                employee_id=request.employee_id,
                company_id=company_id
            )
            
            # 5. Security Gateway (Phase 17)
            from security.gateway import SecurityGateway
            from security.models import SecurityRequest, SecurityContext, ActionType, SecurityDecisionStatus
            
            sec_gateway = SecurityGateway()
            sec_context = SecurityContext(
                organization_id=context.company_id,
                employee_id=context.employee_id,
                task_id=context.task_id,
                capabilities=allowed_tools
            )
            sec_request = SecurityRequest(
                request_id=context.request_id,
                trace_id=context.execution_id,
                context=sec_context,
                action_type=ActionType.TOOL_EXECUTION,
                resource=tool_id,
                intent=_build_semantic_intent(tool_id, request.arguments, context.employee_id, context.task_id),
                payload_metadata=request.arguments,
                tool_id=tool_id
            )
            decision = sec_gateway.evaluate_request(sec_request)
            
            if decision.status != SecurityDecisionStatus.ALLOW:
                return self._error_result(tool_id, f"Security Gateway Denied Execution: {decision.reason}")
            
            # 6. Execute
            return await ToolExecutor.execute(implementation, request.arguments, context)
            
        except ToolError as e:
            return self._error_result(request.tool_name, str(e))
        except Exception as e:
            logger.error(f"CoreToolGateway unexpected error: {e}")
            return self._error_result(request.tool_name, f"Unexpected Gateway Error: {str(e)}")

    def _error_result(self, tool_name: str, error_msg: str) -> ToolResult:
        logger.warning(f"Gateway rejected tool {tool_name}: {error_msg}")
        return ToolResult(
            tool_name=tool_name,
            status="error",
            output={},
            error=error_msg
        )
