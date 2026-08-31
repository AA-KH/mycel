from enum import Enum
from core.errors import AppException

class InvalidStateTransitionError(AppException):
    def __init__(self, current_state: str, next_state: str):
        super().__init__(
            message=f"Invalid transition from {current_state} to {next_state}",
            code="INVALID_STATE_TRANSITION",
            status_code=500
        )


class RuntimeState(str, Enum):
    CREATED = "CREATED"
    INITIALIZING = "INITIALIZING"
    PLANNING = "PLANNING"
    EXECUTING = "EXECUTING"
    WAITING_TOOL = "WAITING_TOOL"
    OBSERVING = "OBSERVING"
    VERIFYING = "VERIFYING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    TIMED_OUT = "TIMED_OUT"

    def can_transition_to(self, next_state: 'RuntimeState') -> bool:
        """Validates state transitions."""
        if self == next_state:
            return True
            
        # Terminal states
        if self in {RuntimeState.COMPLETED, RuntimeState.FAILED, RuntimeState.CANCELLED, RuntimeState.TIMED_OUT}:
            return False

        valid_transitions = {
            RuntimeState.CREATED: {RuntimeState.INITIALIZING, RuntimeState.CANCELLED, RuntimeState.TIMED_OUT},
            RuntimeState.INITIALIZING: {RuntimeState.PLANNING, RuntimeState.FAILED, RuntimeState.CANCELLED, RuntimeState.TIMED_OUT},
            RuntimeState.PLANNING: {RuntimeState.EXECUTING, RuntimeState.FAILED, RuntimeState.CANCELLED, RuntimeState.TIMED_OUT},
            RuntimeState.EXECUTING: {RuntimeState.WAITING_TOOL, RuntimeState.VERIFYING, RuntimeState.FAILED, RuntimeState.CANCELLED, RuntimeState.TIMED_OUT},
            RuntimeState.WAITING_TOOL: {RuntimeState.OBSERVING, RuntimeState.FAILED, RuntimeState.CANCELLED, RuntimeState.TIMED_OUT},
            RuntimeState.OBSERVING: {RuntimeState.EXECUTING, RuntimeState.FAILED, RuntimeState.CANCELLED, RuntimeState.TIMED_OUT},
            RuntimeState.VERIFYING: {RuntimeState.COMPLETED, RuntimeState.EXECUTING, RuntimeState.FAILED, RuntimeState.CANCELLED, RuntimeState.TIMED_OUT},
        }

        return next_state in valid_transitions.get(self, set())
