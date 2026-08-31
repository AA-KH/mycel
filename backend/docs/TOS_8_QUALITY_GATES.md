# Phase TOS 8: Quality Gates

## Overview
Phase TOS 8 successfully establishes a robust Quality Gate System that differentiates "execution completion" from "output success." A pipeline stage may technically finish executing, but it cannot proceed to the next stage (or mark the task complete) unless the `QualityGate` passes.

## Concepts

### Quality Gate
A `QualityGate` defines **what must be true** before a stage result is accepted. It acts as an aggregate container for multiple checks and a singular policy. It is strictly versioned to prevent active pipelines from suddenly failing due to an updated standard.

### Quality Check
A `QualityCheck` maps to an individual executable validation logic (e.g. `EXISTS`, `FORMAT`, `TEST`). Each check has its own required status and severity (INFO, WARNING, ERROR, CRITICAL).

### Quality Policy
A `QualityPolicy` governs how the results of all individual checks collapse into a single final `QualityGateDecision`. E.g., `ALL_REQUIRED_PASS` vs `CRITICAL_FAILURE_BLOCKS`.

### Gate Decision
The output of a Quality Gate execution. Possible decisions:
- `PASS`: Execution may proceed.
- `RETRY`: Execution failed but should be attempted again.
- `BLOCK`: Execution cannot continue until an external condition is resolved.
- `FAIL`: Execution failed irrecoverably.
- `ESCALATE`: A human or superior system must review.
