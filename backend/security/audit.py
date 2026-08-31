import logging
import json
import uuid
from typing import Dict, Any

from security.models import SecurityAuditEvent

logger = logging.getLogger("security.audit")

class AuditLogger:
    """
    Centralized logger for SecurityAuditEvents.
    Redacts sensitive fields before logging.
    """

    REDACTED_KEYS = {"api_key", "password", "token", "secret", "credentials"}

    def log_decision(self, event: SecurityAuditEvent) -> None:
        """Log a security decision securely."""
        sanitized_payload = self._redact(event.request.payload_metadata)
        
        log_entry = {
            "event_id": event.event_id,
            "timestamp": event.timestamp.isoformat(),
            "request_id": event.request.request_id,
            "trace_id": event.request.trace_id,
            "action": event.request.action_type.value,
            "resource": event.request.resource,
            "actor": {
                "agent_id": event.request.context.agent_id,
                "team_id": event.request.context.team_id,
                "organization_id": event.request.context.organization_id
            },
            "intent": event.request.intent,
            "payload_metadata": sanitized_payload,
            "decision": {
                "status": event.decision.status.value,
                "risk_level": event.decision.risk_level.value,
                "reason": event.decision.reason,
                "policy_id": event.decision.policy_id,
                "provider_result": event.decision.provider_result
            }
        }
        
        # Log to secure audit trail (could also push to MongoDB/Elasticsearch here)
        logger.info(f"SECURITY_AUDIT: {json.dumps(log_entry)}")

    def _redact(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively redact sensitive keys from dictionaries."""
        sanitized = {}
        for key, value in data.items():
            if any(redacted in key.lower() for redacted in self.REDACTED_KEYS):
                sanitized[key] = "[REDACTED]"
            elif isinstance(value, dict):
                sanitized[key] = self._redact(value)
            else:
                sanitized[key] = value
        return sanitized
