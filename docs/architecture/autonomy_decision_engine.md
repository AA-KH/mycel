# Autonomy Decision Engine

The `DecisionEngine` is the brain of the Autonomy loop. It maps a `CompanyStateSnapshot` to a single `AutonomyDecision`. 

## Deterministic Priority Stack

To ensure predictable behavior, the decision engine evaluates conditions in a strict priority order. The first matching condition produces the decision.

1.  **SAFETY:** If the kill switch is active, immediately return a `PAUSE` decision (Risk Level: CRITICAL).
2.  **LOOP / ESCALATION:** If a loop is detected or an active escalation exists, return `ESCALATE` or `WAIT` to halt autonomous forward progress.
3.  **BUDGET:** If cost or iterations are exhausted, return `REQUEST_APPROVAL` or `ESCALATE`.
4.  **PLAN REQUIRED:** If no plan exists, return `REPLAN` to generate the initial plan.
5.  **COMPLETE:** If overall progress is 1.0 and no blockers exist, return `COMPLETE` to trigger the final validation gate.
6.  **FAILED TASKS:** If tasks have failed (after retries), return `REPLAN`.
7.  **BLOCKED:** If there are blocked tasks and no active tasks, return `ESCALATE`.
8.  **WAITING ON ACTIVE:** If tasks are executing but no other tasks have satisfied dependencies, return `WAIT`.
9.  **CREATE NEXT TASK:** If a descriptor in the plan has all dependencies met, return `CREATE_TASK`.
10. **DEFAULT:** Return `WAIT`.

## Evidence and Traceability

Every `AutonomyDecision` must include:
*   `decision_type`: An enum (e.g., `CREATE_TASK`).
*   `reason`: Human-readable explanation.
*   `evidence`: JSON dict containing the exact variables that triggered the rule (e.g., `{"progress": 1.0}`).

LLMs are NOT used in the core decision engine to prevent unpredictable "hallucinated" autonomy.
