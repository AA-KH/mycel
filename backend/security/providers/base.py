from abc import ABC, abstractmethod
from typing import Optional
from security.models import SecurityRequest, SecurityDecisionStatus

class SecurityProvider(ABC):
    """Abstract interface for external security providers (e.g. ArmorIQ)."""
    
    @abstractmethod
    def evaluate(self, request: SecurityRequest) -> tuple[SecurityDecisionStatus, str]:
        """
        Evaluate the security request against the provider.
        Returns a tuple of (DecisionStatus, Reason/ProviderResult).
        """
        pass
