from enum import Enum

class ReasoningState(Enum):
    INITIALIZING = "initializing"
    EXPLORING = "exploring"
    DECOMPOSING = "decomposing"
    PLANNING = "planning"
    READY = "ready"
    EXECUTING = "executing"
    OBSERVING = "observing"
    CRITIQUING = "critiquing"
    REVISING = "revising"
    VERIFYING = "verifying"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"

    def can_transition_to(self, new_state: 'ReasoningState') -> bool:
        """
        Validates whether the transition from self to new_state is allowed.
        """
        # Terminal states
        if self in (ReasoningState.COMPLETED, ReasoningState.FAILED, ReasoningState.BLOCKED):
            return False
            
        # Any active state can transition to FAILED or BLOCKED
        if new_state in (ReasoningState.FAILED, ReasoningState.BLOCKED):
            return True

        valid_transitions = {
            ReasoningState.INITIALIZING: [ReasoningState.EXPLORING, ReasoningState.DECOMPOSING],
            ReasoningState.EXPLORING: [ReasoningState.DECOMPOSING],
            ReasoningState.DECOMPOSING: [ReasoningState.PLANNING],
            ReasoningState.PLANNING: [ReasoningState.READY],
            ReasoningState.READY: [ReasoningState.EXECUTING, ReasoningState.COMPLETED],
            ReasoningState.EXECUTING: [ReasoningState.OBSERVING],
            ReasoningState.OBSERVING: [ReasoningState.CRITIQUING, ReasoningState.VERIFYING],
            ReasoningState.CRITIQUING: [ReasoningState.REVISING, ReasoningState.EXECUTING, ReasoningState.VERIFYING],
            ReasoningState.REVISING: [ReasoningState.READY, ReasoningState.EXECUTING],
            ReasoningState.VERIFYING: [ReasoningState.VALIDATING, ReasoningState.CRITIQUING],
            ReasoningState.VALIDATING: [ReasoningState.COMPLETED, ReasoningState.CRITIQUING],
        }

        return new_state in valid_transitions.get(self, [])
