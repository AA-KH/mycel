# Quality Check Catalogue

The following check types form the foundational components of the Quality Gate system.

## Check Types Implemented (TOS 8)

### `EXISTS`
Verifies that an expected artifact reference was successfully registered in the context.
**Configuration:** `artifact_key: str`

### `FORMAT`
Checks if an artifact is of the correct format (e.g., `.mp4`, `.pdf`). Delegates validation to the existing `ArtifactSystem`.
**Configuration:** `artifact_key: str`, `expected_format: str`

## Future Check Types
- `SCHEMA`: Validates JSON outputs against a JSON schema.
- `SIZE`: Enforces min/max byte sizes for deliverables.
- `CITATION`: Enforces that all claims in a research report possess verified citations.
- `TEST`: Evaluates software test runners output for passing/failing tests.
- `LLM_REVIEW`: Passes the context to a specialized LLM Reviewer returning a structured score and decision.
