"""
DEPRECATED: Legacy Agent Adapter.
Used to transition between the Phase 3 Employee Definitions and the old GenericAgent system.
This file provides utilities for the eventual full transition to Agent Runtime.
Slated for removal in future TOS phases.
"""

from typing import Optional
from workforce.employees.registry import EmployeeRegistry
from workforce.employees.models import Employee
from agents.base_agent import BaseAgent
from agents.team_agents import TEAM_REGISTRY, GenericAgent

class LegacyAgentAdapter:
    """
    Adapter that will eventually take an Employee definition and spin up an equivalent
    execution runtime, bridging the gap between old and new systems.
    
    For now, this provides a pathway for the ManagerAgent to look up an employee
    from the registry before falling back to the old TEAM_REGISTRY.
    """
    def __init__(self, registry: EmployeeRegistry):
        self.registry = registry

    async def get_agent_for_task(self, company_id: str, role_title: str, task_id: str, user_id: str = "system") -> BaseAgent:
        """
        Attempts to find a registered Employee for the task.
        If found, constructs a GenericAgent using the employee's title and identity summary.
        If not, falls back to the hardcoded TEAM_REGISTRY.
        """
        employee = await self.registry.resolve_by_role(company_id, role_title)
        if employee:
            # We found an employee, construct a dynamic agent from their profile.
            system_prompt = (
                f"You are {employee.name}, a {employee.identity.title} at Mycel.\n"
                f"Personality: {employee.identity.personality}\n"
                f"Communication Style: {employee.identity.communication_style}\n"
                f"Role Summary: {employee.identity.summary}\n\n"
                "Your job is to execute tasks related to your specific role with elite proficiency.\n"
                "Guidelines:\n- Follow instructions carefully.\n- Provide high-quality output."
            )
            agent = GenericAgent(team_name=employee.identity.title.lower().replace(" ", "-"), task_id=task_id, user_id=user_id)
            agent.name = employee.display_name
            agent.system_prompt = system_prompt
            return agent
        
        # Fallback to the legacy static registry if no employee match is found
        cls = TEAM_REGISTRY.get(role_title.lower())
        if cls:
            return cls(task_id=task_id, user_id=user_id)
        
        # Absolute fallback to GenericAgent
        return GenericAgent(role_title.lower(), task_id=task_id, user_id=user_id)


from agents.runtime.lifecycle import AgentRuntime
from agents.runtime.context import ExecutionContext
from agents.runtime.snapshot import ExecutionSnapshot
from agents.runtime.interfaces import ToolGateway, ResultVerifier, MemoryProvider, ArtifactManager
from agents.runtime.result import ToolRequest, ToolResult, VerificationResult
from typing import Dict, Any

# Minimal no-op mock implementations for testing and legacy bridging
class NoOpToolGateway(ToolGateway):
    async def execute(self, request: ToolRequest) -> ToolResult:
        return ToolResult(tool_name=request.tool_name, status="success", output={"message": f"Mock executed {request.tool_name}"})

class CoreResultVerifier(ResultVerifier):
    async def verify(self, task: Dict[str, Any], result: Any, expected_output: Dict[str, Any]) -> VerificationResult:
        # Check if task expected an artifact
        if expected_output and expected_output.get("type") in ["video", "image", "audio", "document", "pdf", "presentation"]:
            # Task expects an artifact. We must find it in the result.
            # In our system, the LLM usually outputs {"artifact": {"artifact_id": "art_..."}}
            artifact_data = None
            if isinstance(result, dict) and "artifact" in result:
                artifact_data = result["artifact"]
            
            if not artifact_data or "artifact_id" not in artifact_data:
                return VerificationResult(status="failed", reason=f"Task expected artifact of type {expected_output['type']}, but none was returned.")
                
            artifact_id = artifact_data["artifact_id"]
            from artifacts import get_artifact_service
            service = get_artifact_service()
            
            artifact = await service.get_artifact(artifact_id)
            if not artifact:
                return VerificationResult(status="failed", reason=f"Artifact {artifact_id} not found in repository.")
                
            if artifact.status.value != "ready":
                return VerificationResult(status="failed", reason=f"Artifact {artifact_id} is in status {artifact.status.value}, expected ready.")
                
            if artifact.type != expected_output["type"]:
                return VerificationResult(status="failed", reason=f"Artifact type {artifact.type} does not match expected type {expected_output['type']}.")
                
        return VerificationResult(status="passed")

class NoOpMemoryProvider(MemoryProvider):
    async def get_context(self, employee_id: str, task_id: str, query: str) -> str:
        return ""
    async def store_memory(self, employee_id: str, task_id: str, content: str) -> None:
        pass

class NoOpArtifactManager(ArtifactManager):
    async def register_artifact(self, execution_id: str, content: Any, artifact_type: str) -> str:
        return f"artifact_{execution_id}"

class AgentRuntimeAdapter(BaseAgent):
    """
    Acts like a legacy BaseAgent but routes execution through the new AgentRuntime.
    This allows existing orchestrators to use the new system transparently.
    """
    def __init__(self, employee: Employee, task_id: str, company_id: str, user_id: str = "system"):
        # BaseAgent expects name, role, system_prompt. 
        # We pass dummy system_prompt because the runtime builds its own.
        super().__init__(name=employee.display_name, role=employee.identity.title, system_prompt="", user_id=user_id)
        
        self.employee = employee
        self.task_id = task_id
        self.company_id = company_id
        
        from tools.gateway import CoreToolGateway
        
        # Instantiate the new runtime with NoOp dependencies (for Phase 4) except ToolGateway and Verifier
        self.runtime = AgentRuntime(
            tool_gateway=CoreToolGateway(),
            result_verifier=CoreResultVerifier(),
            memory_provider=NoOpMemoryProvider(),
            artifact_manager=NoOpArtifactManager()
        )

    async def run_task(self, task_description: str, model: str = "openai/gpt-oss-120b"):
        """
        Overrides the BaseAgent run_task to use the Phase 4 AgentRuntime.
        """
        snapshot = ExecutionSnapshot.from_employee(self.employee)
        
        # The runtime creates a context
        context = ExecutionContext(
            task_id=self.task_id,
            employee_id=self.employee.id,
            company_id=self.company_id,
            user_id=self.user_id
        )
        
        task_dict = {
            "task_id": self.task_id,
            "title": "Legacy Task",
            "description": task_description,
            "expected_output": {"type": "text"}
        }
        
        # We can also map 'working' to the UI before starting, handled by runtime events
        result = await self.runtime.execute(snapshot, task_dict, context)
        
        if result.status == "failed":
            raise Exception(result.error)
            
        # Extract the content from the structured JSON output to return strings to legacy callers
        if isinstance(result.output, dict) and "content" in result.output:
            return result.output["content"]
        elif isinstance(result.output, dict) and "message" in result.output:
            return result.output["message"]
        elif isinstance(result.output, str):
            return result.output
        else:
            import json
            return json.dumps(result.output)

