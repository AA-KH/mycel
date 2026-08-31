# Output Validation

The `OutputContractValidationService` verifies an actual produced context/artifact against an `OutputContract`.

## Flow
1. **Agent Produces Deliverable** -> Yields an actual output payload (typically an `ArtifactReference`).
2. **Output Contract Validation** -> `validate(expected_contract, actual_output)`.
3. Checks run for `ArtifactPolicy` (Is it missing?), `formats` (Does it match?), `metadata_requirements` (Does resolution match?).
4. Yields an `OutputValidationResult` containing a `valid` boolean and a list of `OutputViolation` instances.
5. If `valid=True`, the execution moves to the **Quality Gate** evaluation (TOS 8).
6. Task Completion occurs only if **Output Contract PASSES** AND **Quality Gate PASSES**.
