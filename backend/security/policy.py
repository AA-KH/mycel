from typing import Tuple
from security.models import SecurityRequest, SecurityDecisionStatus

class PolicyEngine:
    """
    Enforces authorization rules and least privilege constraints.
    Returns (Status, Reason).
    """

    def evaluate_policy(self, request: SecurityRequest) -> Tuple[SecurityDecisionStatus, str]:
        # 1. Environment Protection
        if "prod" in request.context.environment.lower():
            if "deploy_prod" not in request.context.capabilities:
                return SecurityDecisionStatus.DENY, "Agent lacks 'deploy_prod' capability for production environment."
                
        # 2. Tool Execution Scopes
        if request.action_type == "TOOL_EXECUTION":
            if request.tool_id and request.tool_id not in request.context.capabilities:
                return SecurityDecisionStatus.DENY, f"Agent is not authorized to use tool '{request.tool_id}'."
                
        # 3. Cross-Team Boundary Check
        if request.action_type == "AGENT_HANDOFF":
            # If the user context doesn't have cross-team collaboration ability and it's attempting to handoff outside
            if "cross_team_handoff" not in request.context.capabilities:
                if request.target_agent_id and request.context.team_id:
                    # In a real implementation, we'd check if target_agent_id is in the same team
                    # For now, we assume if target_agent_id is present, it must be validated
                    pass 
            
        # By default, ALLOW if no restrictive policies match (RiskEngine/ArmorIQ will catch the rest)
        return SecurityDecisionStatus.ALLOW, "Passed local policy checks."
