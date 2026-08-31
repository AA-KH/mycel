# Pipeline Execution Model

The Pipeline Execution Model (`PipelineExecutor`) is deliberately designed to act as an abstract state machine wrapper rather than a fully-fledged distributed multi-agent orchestrator.

## State Tracking
- **`PipelineExecution`**: Tracks the overall `execution_id`, the active version of the pipeline, and high-level success/failure.
- **`StageExecutionState`**: Tracks the individual attempts, status, and output references (using `ArtifactReference`, never raw files) for a specific stage.

## Transitions
Execution states strictly flow through predictable transitions:
`PENDING` -> `RUNNING` -> `COMPLETED` | `FAILED`

## Pipeline Completion Guarantee
A pipeline is not considered genuinely `COMPLETED` merely if all stages return a successful status. The final orchestration runtime MUST verify that the `PipelineOutputContract` has been physically satisfied (e.g., the requested `video` artifact actually exists and is validated by the `ArtifactSystem`).
