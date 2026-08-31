import uuid
from typing import Optional
from core.config import settings

from security.models import SecurityRequest, SecurityDecision, SecurityDecisionStatus, SecurityAuditEvent
from security.intent import IntentValidator
from security.policy import PolicyEngine
from security.risk import RiskEngine
from security.audit import AuditLogger

# Providers
from security.providers.base import SecurityProvider
from security.providers.mock import MockSecurityProvider
from security.providers.armoriq import ArmorIQAdapter


class SecurityGateway:
    """
    Centralized Security Gateway.
    All high-risk execution boundaries must pass through this gateway.
    """
    
    def __init__(self, provider: Optional[SecurityProvider] = None):
        self.intent_validator = IntentValidator()
        self.policy_engine = PolicyEngine()
        self.risk_engine = RiskEngine()
        self.audit_logger = AuditLogger()
        
        # Determine provider based on configuration if not injected
        if provider:
            self.provider = provider
        else:
            mode = getattr(settings, 'security_provider_mode', 'armoriq').lower()
            if mode == 'mock':
                self.provider = MockSecurityProvider()
            else:
                self.provider = ArmorIQAdapter()

    def evaluate_request(self, request: SecurityRequest) -> SecurityDecision:
        """
        Evaluate a security request across Intent, Policy, Risk, and ArmorIQ.
        """
        decision_id = str(uuid.uuid4())
        
        # 1. Intent Validation
        intent_status, intent_reason = self.intent_validator.validate(request)
        if intent_status != SecurityDecisionStatus.ALLOW:
            return self._finalize_decision(request, decision_id, intent_status, intent_reason, self.risk_engine.evaluate_risk(request))

        # 2. Policy Engine (Least Privilege)
        policy_status, policy_reason = self.policy_engine.evaluate_policy(request)
        if policy_status != SecurityDecisionStatus.ALLOW:
            return self._finalize_decision(request, decision_id, policy_status, policy_reason, self.risk_engine.evaluate_risk(request))

        # 3. Risk Engine
        risk_level = self.risk_engine.evaluate_risk(request)
        
        # 4. External Provider (ArmorIQ)
        provider_status, provider_reason = self.provider.evaluate(request)
        
        # Final evaluation logic based on provider and risk
        final_status = provider_status
        final_reason = f"Provider: {provider_reason}"
        
        # If provider says allow, but risk is CRITICAL, we might STILL require human approval based on internal policy.
        # But for now, we trust the provider's ultimate judgement if it was ALLOW.
        
        return self._finalize_decision(request, decision_id, final_status, final_reason, risk_level, provider_result=provider_status.value)
        
    def _finalize_decision(self, request: SecurityRequest, decision_id: str, status: SecurityDecisionStatus, reason: str, risk_level, provider_result: Optional[str] = None) -> SecurityDecision:
        decision = SecurityDecision(
            decision_id=decision_id,
            request_id=request.request_id,
            status=status,
            reason=reason,
            risk_level=risk_level,
            provider_result=provider_result
        )
        
        # Audit
        event = SecurityAuditEvent(
            event_id=str(uuid.uuid4()),
            request=request,
            decision=decision
        )
        self.audit_logger.log_decision(event)
        
        decision.audit_reference = event.event_id
        return decision
