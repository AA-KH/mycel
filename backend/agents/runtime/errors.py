from core.errors import AppException

class ExecutionError(AppException):
    def __init__(self, message: str, execution_id: str = None):
        super().__init__(
            message=message,
            code="EXECUTION_ERROR",
            status_code=500
        )
        self.execution_id = execution_id

class EmployeeResolutionError(AppException):
    def __init__(self, message: str):
        super().__init__(
            message=message,
            code="EMPLOYEE_RESOLUTION_ERROR",
            status_code=400
        )

class ReasoningError(AppException):
    def __init__(self, message: str):
        super().__init__(
            message=message,
            code="REASONING_ERROR",
            status_code=500
        )

class ToolExecutionError(AppException):
    def __init__(self, message: str, tool_name: str = None):
        super().__init__(
            message=message,
            code="TOOL_EXECUTION_ERROR",
            status_code=500
        )
        self.tool_name = tool_name

class VerificationError(AppException):
    def __init__(self, message: str):
        super().__init__(
            message=message,
            code="VERIFICATION_ERROR",
            status_code=400
        )

class ExecutionTimeoutError(AppException):
    def __init__(self, message: str):
        super().__init__(
            message=message,
            code="EXECUTION_TIMEOUT",
            status_code=408
        )

class ExecutionCancelledError(AppException):
    def __init__(self, message: str):
        super().__init__(
            message=message,
            code="EXECUTION_CANCELLED",
            status_code=499
        )
