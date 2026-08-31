# Quality Gate Architecture

## Flow
The canonical quality gate evaluation flow during pipeline execution:

```
Stage
 ↓
Execution
 ↓
Output
 ↓
Quality Gate
 ↓
QualityGateExecutor evaluates all QualityChecks
 ↓
QualityPolicy evaluates all QualityCheckResults
 ↓
Decision
 ├── PASS     --> Next Stage
 ├── RETRY    --> Attempt Stage Again
 ├── BLOCK    --> Pause Pipeline
 ├── FAIL     --> Fail Pipeline
 └── ESCALATE --> Escalate for Human/LLM Review
```

## Integration with Pipelines
A `PipelineStage` (from TOS 6) can attach multiple gate pointers:
- `pre_gate_id`: Checked before execution begins (e.g., validate input).
- `post_gate_id`: Checked after execution finishes (e.g., validate output).

The overall `TeamPipeline` can attach `pipeline_gate_ids` which execute at the very end to validate the final task deliverable.

## Artifact System Independence
`QualityGate` validates conditional state but DOES NOT physically parse or interact with Cloudinary. It delegates artifact checks to the existing `ArtifactService` via the `ArtifactValidationResult`.
