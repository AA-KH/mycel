from typing import Tuple
from security.models import SecurityRequest, SecurityDecisionStatus

class IntentValidator:
    """
    Validates that the stated intent is present and makes sense for the requested action.
    """

    def validate(self, request: SecurityRequest) -> Tuple[SecurityDecisionStatus, str]:
        # Missing intent is a fail closed condition
        if not request.intent or len(request.intent.strip()) < 3:
            return SecurityDecisionStatus.DENY, "Missing or insufficient intent description."
            
        # Basic prompt injection checks (very lightweight regex/keyword checks)
        intent_lower = request.intent.lower()
        if "ignore previous instructions" in intent_lower or "bypass security" in intent_lower:
            return SecurityDecisionStatus.DENY, "Malicious intent detected (Prompt Injection signature)."
            
        return SecurityDecisionStatus.ALLOW, "Intent validated."
