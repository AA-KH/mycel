class SecurityDeniedError(Exception):
    """Raised when a security request is explicitly denied."""
    pass

class SecurityApprovalRequired(Exception):
    """Raised when a high-risk security request requires human approval."""
    pass

class SecurityProviderError(Exception):
    """Raised when the security provider (e.g., ArmorIQ) fails or times out."""
    pass

class SecurityContextError(Exception):
    """Raised when the provided security context is invalid or missing required fields."""
    pass

class SecurityPolicyError(Exception):
    """Raised when there is a conflict or error in evaluating policies."""
    pass

class SecurityRiskError(Exception):
    """Raised when risk evaluation fails."""
    pass
