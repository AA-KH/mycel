import logging
from security.providers.base import SecurityProvider
from security.models import SecurityRequest, SecurityDecisionStatus, RiskLevel
from security.exceptions import SecurityProviderError
from core.config import settings
import uuid

logger = logging.getLogger(__name__)

try:
    from armoriq_sdk import ArmorIQClient, ArmorIQException
    # We initialize it conditionally based on config
    HAS_ARMORIQ = True
except ImportError:
    HAS_ARMORIQ = False

class ArmorIQAdapter(SecurityProvider):
    """
    Production-grade adapter for the ArmorIQ security SDK.
    Enforces bounded timeouts and fails closed for critical risks.
    """
    
    def __init__(self):
        if not HAS_ARMORIQ:
            logger.warning("ArmorIQ SDK not installed. ArmorIQAdapter will fail closed.")
            self.client = None
        elif not settings.armoriq_api_key:
            logger.warning("ArmorIQ API key not configured. ArmorIQAdapter will fail closed.")
            self.client = None
        else:
            self.client = ArmorIQClient(api_key=settings.armoriq_api_key, timeout=getattr(settings, 'armoriq_timeout_ms', 5000) / 1000.0)

    def evaluate(self, request: SecurityRequest) -> tuple[SecurityDecisionStatus, str]:
        if not self.client:
            return self._handle_provider_outage(request.risk_level, "ArmorIQ Client not initialized or missing credentials.")

        try:
            # We don't send the entire raw payload. We send structured intent and metadata.
            aq_payload = {
                "request_id": request.request_id,
                "actor": request.context.agent_id or "unknown",
                "action": request.action_type.value,
                "intent": request.intent,
                "environment": request.context.environment
            }
            
            # Start a lightweight stateless evaluation
            result = self.client.evaluate_intent(payload=aq_payload)
            
            if result.get("decision") == "ALLOW":
                return SecurityDecisionStatus.ALLOW, result.get("reason", "ArmorIQ Approved")
            elif result.get("decision") == "REVIEW":
                return SecurityDecisionStatus.REQUIRE_APPROVAL, result.get("reason", "ArmorIQ requires human review")
            else:
                # DENY or UNKNOWN
                return SecurityDecisionStatus.DENY, result.get("reason", "ArmorIQ Denied")
                
        except Exception as e:
            logger.error(f"ArmorIQProvider encountered an error: {e}")
            from security.models import RiskLevel
            return self._handle_provider_outage(RiskLevel.HIGH, str(e))
            
    def _handle_provider_outage(self, risk_level: RiskLevel, error_msg: str) -> tuple[SecurityDecisionStatus, str]:
        """
        Fails closed for HIGH and CRITICAL risks. 
        May allow graceful degradation for LOW risks depending on policy, but default to safe.
        """
        if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            logger.error(f"Failing closed due to Security Provider Outage on {risk_level.value} risk action: {error_msg}")
            return SecurityDecisionStatus.DENY, f"Provider outage. Action denied due to {risk_level.value} risk."
        else:
            # For LOW/MEDIUM risks, we fail closed by default unless explicit config allows bypass
            # In a true Zero Trust system, we still deny.
            return SecurityDecisionStatus.DENY, f"Provider outage. Failing closed for {risk_level.value} risk."
