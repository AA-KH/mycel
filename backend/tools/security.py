from typing import Dict, Any, List
from .models import ToolDefinition, ToolPermissionDeniedError, ToolValidationError, ToolApprovalRequiredError
from agents.runtime.result import ToolRequest

class ToolSecurityPolicy:
    """
    Enforces permissions, capabilities, and argument schema validation.
    """
    
    @staticmethod
    def validate_request(request: ToolRequest, definition: ToolDefinition, employee_tool_ids: List[str]) -> None:
        """
        Validates whether the request is allowed to execute.
        Raises ToolError subclasses if validation fails.
        """
        
        # 1. Availability Check
        if not definition.enabled:
            raise ToolPermissionDeniedError(f"Tool {definition.id} is currently disabled globally.", definition.id)
            
        # 2. Permission Check (Does the employee have this tool?)
        if definition.id not in employee_tool_ids:
            raise ToolPermissionDeniedError(f"Employee {request.employee_id} does not have permission to use {definition.id}.", definition.id)
            
        # 3. Schema Validation
        # In a full system we would use jsonschema or Pydantic dynamic models
        # For Phase 6 we do a basic required keys check based on the schema
        required_keys = definition.input_schema.get("required", [])
        for key in required_keys:
            if key not in request.arguments:
                raise ToolValidationError(f"Missing required argument: {key}", definition.id)
                
        # 4. Approval Check
        if definition.requires_approval:
            # We don't have human approval implemented, but we enforce the contract
            raise ToolApprovalRequiredError(f"Tool {definition.id} requires explicit human approval.", definition.id)
            
        # 5. Risk Assessment (just an audit hook for now)
        if definition.risk_level in ("high", "critical"):
            # Would emit a high risk audit event here
            pass

    @staticmethod
    def validate_ssrf(url: str) -> None:
        """
        Basic SSRF validation for web tools.
        """
        import urllib.parse
        parsed = urllib.parse.urlparse(url)
        hostname = parsed.hostname or ""
        hostname = hostname.lower()
        
        blocked_hosts = [
            "localhost", "127.0.0.1", "0.0.0.0", 
            "169.254.169.254", # AWS metadata
            "metadata.google.internal" # GCP metadata
        ]
        
        if hostname in blocked_hosts or hostname.startswith("192.168.") or hostname.startswith("10."):
            raise ToolValidationError(f"Access to internal or restricted host {hostname} is blocked.", "web")
