from security.providers.base import SecurityProvider
from security.models import SecurityRequest, SecurityDecisionStatus
import logging

logger = logging.getLogger(__name__)

class MockSecurityProvider(SecurityProvider):
    """
    Mock provider for local development and testing.
    Never use in production.
    """
    
    def evaluate(self, request: SecurityRequest) -> tuple[SecurityDecisionStatus, str]:
        intent_lower = request.intent.lower()
        
        # Simulate ArmorIQ finding an issue
        if "hack" in intent_lower or "malicious" in intent_lower:
            logger.warning("MockSecurityProvider: Detected simulated malicious intent.")
            return SecurityDecisionStatus.DENY, "Mock Provider: Denied due to suspicious keyword."
            
        # Simulate timeout
        if "timeout" in intent_lower:
            return SecurityDecisionStatus.ERROR, "Mock Provider: Simulated timeout."
            
        # Simulate requiring approval
        if "deploy" in intent_lower:
            return SecurityDecisionStatus.REQUIRE_APPROVAL, "Mock Provider: Deployment requires human approval."
            
        return SecurityDecisionStatus.ALLOW, "Mock Provider: Allowed."
