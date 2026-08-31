# Quality Failure Handling

## Decisions

### `RETRY`
A quality failure may trigger a retry. This is strictly bounded by a `max_attempts` limit on the pipeline execution side to prevent infinite loops (e.g., generation fails quality, attempts generation again, fails again... caps at 3).

### `BLOCK`
Occurs when a critical required condition cannot be resolved by the agent automatically, such as a missing external dependency. The pipeline remains active but halted.

### `FAIL`
A hard failure that aborts the pipeline. Occurs when retries are exhausted or when an irrecoverable `CRITICAL` check fails under an `ALL_REQUIRED_PASS` policy.

### `ESCALATE`
Signals that the automated quality checks cannot confidently decide. Used for subjective evaluations, high-risk legal documents, or brand approvals. Awaiting future UI implementation for human override.
