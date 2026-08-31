"""
Centralized Error Handling for Mycel.
Provides a standard exception hierarchy and formatting mechanism.
"""

from typing import Any, Dict, Optional


class AppException(Exception):
    """
    Base class for all application-specific exceptions.
    """
    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}

    def to_dict(self, request_id: Optional[str] = None) -> Dict[str, Any]:
        """Convert exception to standard JSON format."""
        return {
            "success": False,
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
            },
            "request_id": request_id,
        }


class ConfigurationError(AppException):
    """Raised when application configuration is invalid."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="CONFIG_ERROR", status_code=500, details=details)


class DatabaseError(AppException):
    """Raised when a database operation fails."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="DATABASE_ERROR", status_code=500, details=details)


class QueueError(AppException):
    """Raised when a message broker operation fails."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="QUEUE_ERROR", status_code=500, details=details)


class AuthenticationError(AppException):
    """Raised when authentication fails."""
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="AUTH_ERROR", status_code=401, details=details)


class AuthorizationError(AppException):
    """Raised when a user or agent lacks permissions."""
    def __init__(self, message: str = "Permission denied", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="PERMISSION_DENIED", status_code=403, details=details)


class ValidationError(AppException):
    """Raised when input validation fails."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="VALIDATION_ERROR", status_code=400, details=details)


class NotFoundError(AppException):
    """Raised when a resource is not found."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="NOT_FOUND", status_code=404, details=details)


class TaskError(AppException):
    """Raised when task processing fails."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="TASK_ERROR", status_code=400, details=details)


class AgentError(AppException):
    """Raised when agent execution fails."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="AGENT_ERROR", status_code=500, details=details)


class ToolError(AppException):
    """Raised when a tool execution fails."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="TOOL_ERROR", status_code=400, details=details)


class ArtifactError(AppException):
    """Raised when artifact validation or storage fails."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="ARTIFACT_ERROR", status_code=500, details=details)


class DomainError(AppException):
    """Raised when a business domain rule is violated."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="DOMAIN_ERROR", status_code=400, details=details)

