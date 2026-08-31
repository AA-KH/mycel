# Autonomy State Observation

The Autonomy layer acts on a `CompanyStateSnapshot`, not on raw database records. This decoupling ensures the engine remains fast, testable, and isolated from the operational data stores of other subsystems.

## State Observer

The `CompanyStateObserver` builds the snapshot using data injected from the Team Operating System (TOS). 

It aggregates:
1.  **Task States:** Which tasks are active, completed, or failed.
2.  **Quality Results:** Whether completed tasks passed their quality gates.
3.  **Budget State:** How much cost and iteration budget has been consumed.
4.  **Escalations:** Any active blockers requiring human attention.

## Progress Tracking

Progress is computed strictly based on **meaningful work completion**.
The `ProgressTracker` bounds progress from 0.0 to 1.0.

*   **Completion Criteria:** A task only counts toward progress if it is technically COMPLETED **and** it passed its Quality Gate. 
*   **Blocked Penalties:** If tasks are blocked, progress is artificially capped (e.g., at 0.95) to prevent the system from claiming 100% completion while blockers exist.
*   **Milestone Weighting:** Overall progress is the weighted average of milestone completion percentages.

## Completion Validator

An objective is only marked COMPLETED if the `ObjectiveCompletionValidator` confirms:
1.  All milestones are marked COMPLETED.
2.  All required outputs (artifacts) are present.
3.  No tasks are in a failed state.
4.  All explicit `SuccessCriteria` defined on the objective have been met.
