from security.models import SecurityRequest, ActionType, RiskLevel

class RiskEngine:
    """
    Evaluates the inherent risk of a security request.
    """

    def evaluate_risk(self, request: SecurityRequest) -> RiskLevel:
        action = request.action_type
        
        # Critical Risks
        if action == ActionType.DEPLOYMENT and "prod" in request.context.environment.lower():
            return RiskLevel.CRITICAL
        if action == ActionType.FILE_OPERATION and "delete" in request.intent.lower():
            return RiskLevel.CRITICAL
            
        # High Risks
        if action == ActionType.EXTERNAL_API_CALL:
            return RiskLevel.HIGH
        if action == ActionType.DEPLOYMENT:
            return RiskLevel.HIGH
        if action == ActionType.DATABASE_OPERATION and any(k in request.intent.lower() for k in ["drop", "truncate", "delete", "update", "insert"]):
            return RiskLevel.HIGH
            
        # Medium Risks
        if action == ActionType.EXTERNAL_MESSAGE:
            return RiskLevel.MEDIUM
        if action == ActionType.AGENT_HANDOFF:
            # Handoff across team boundaries is higher risk
            target_agent = request.target_agent_id
            if request.context.team_id and target_agent and "cross-team" in request.payload_metadata.get("tags", []):
                return RiskLevel.MEDIUM
            return RiskLevel.LOW
            
        # Low Risks
        return RiskLevel.LOW
