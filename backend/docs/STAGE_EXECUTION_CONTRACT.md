# Stage Execution Contract

## Declarative Boundaries
The `StageDefinition` is strictly declarative. Execution remains the sole responsibility of the `PipelineExecutor`, `AgentRuntime`, and `ToolExecutor`.

## Stage Validation
The `StageValidationContract` ensures that a stage cannot be lazily marked `COMPLETED` merely because an LLM returned arbitrary text.
If `artifact_required` is true, the `PipelineExecutor` will eventually verify that an `ArtifactReference` was deposited into the context.

## Failure Policies
The `StageFailurePolicy` dictates exactly how orchestrators handle failure.
- `retryable`: Boolean indicating if the stage can be attempted again.
- `max_attempts`: Int indicating max retries (hard-capped to 5 by validation logic).
- `fail_pipeline`: Boolean indicating if failure of this stage should crash the entire pipeline graph.
