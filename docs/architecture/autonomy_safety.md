# Autonomy Loop Safety & Invariants

The `AutonomyEngine` is designed to be fail-safe. If the system gets confused, it stops. It does not guess.

## Loop Detection

A common failure mode for autonomous agents is getting stuck in an infinite retry or replanning loop. The `LoopDetector` analyzes the audit history of `AutonomyDecision`s and task failures to prevent this.

**Triggers:**
*   **Task Failure Loop:** A specific task fails more than the allowed `max_retries_per_task`.
*   **Replan Loop:** The engine attempts to replan more than `max_replan_count`.
*   **Decision Loop:** The exact same non-waiting decision (e.g., `CREATE_TASK`) is produced multiple times consecutively without state changing.

When a loop is detected, the `DecisionEngine` overrides its normal priority and returns `ESCALATE` (Risk Level: HIGH).

## Failure Analysis

When a task fails, the `ObjectiveFailureAnalyzer` classifies the failure to guide the engine.

*   **TRANSIENT** (e.g., API timeout) → `RETRY`
*   **RESOURCE** (e.g., Employee busy) → `RETRY`
*   **CAPABILITY** (e.g., No agent has the skill) → `REPLAN`
*   **QUALITY** (e.g., Artifact rejected) → `REPLAN`
*   **POLICY / SYSTEM** → `ESCALATE` (Non-recoverable)

## The Kill Switch

The Kill Switch is absolute. If `kill_switch_active` is True:
1.  The `AutonomyEngine` forces a `PAUSE` decision.
2.  The `PolicyEngine` blocks any new task creation.
3.  The `ApprovalGate` treats `PAUSE` as a `READ_ONLY` action, meaning it bypasses any approval requirements and executes instantly.

## Architectural Invariants

*   **History is Append-Only:** Plans are versioned, and decisions are recorded in an append-only audit log.
*   **Autonomy is a Consumer:** It requests tasks via the Orchestrator, resources via the Talent Market, and evaluations via Quality. It does not re-implement them.
*   **Least Privilege:** The engine runs with the permissions granted by the `AutonomyPolicy`. It cannot escalate itself.
