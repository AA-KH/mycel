# Autonomy Policy & Safety

The autonomy layer operates under strict constraints to prevent runaway resource consumption or dangerous actions. This is handled by the `AutonomyPolicyEngine` and the `ApprovalGate`.

## Policy Engine

The `PolicyEngine` evaluates every proposed decision against `AutonomyPolicy`. It acts as a hard boundary.

**Evaluated Limits:**
*   **Kill Switch:** Absolute veto.
*   **Concurrency Limits:** `max_concurrent_tasks` and `max_concurrent_agents` prevent the system from overwhelming the infrastructure.
*   **Budget Limits:** `max_cost` is tracked across all tasks in the objective. Once exhausted, the engine cannot issue `CREATE_TASK`.
*   **Iteration Limits:** `max_iterations` prevents the engine from infinite looping if it gets stuck in a non-productive state.

The Policy Engine is read-only. The autonomy engine cannot modify its own constraints.

## Approval Gate

Even if an action is within policy limits, it may require human approval based on its risk and the objective's `AutonomyLevel`.

**Autonomy Levels:**
*   **MANUAL:** All actions require approval.
*   **ASSISTED:** All actions require approval.
*   **SUPERVISED:** Actions meeting or exceeding the `require_approval_threshold` (e.g., HIGH risk) require approval.
*   **AUTONOMOUS:** Only CRITICAL or IRREVERSIBLE actions require approval.

**Action Categories:**
*   `READ_ONLY` (e.g., WAIT) never requires approval.
*   `REVERSIBLE` (e.g., CREATE_TASK) depends on the threshold.
*   `IRREVERSIBLE` (e.g., CANCEL) requires approval by default, unless the policy explicitly allows them.

If the Approval Gate flags an action, the decision is converted to `REQUEST_APPROVAL`. Execution pauses until a human user resolves the pending action.
