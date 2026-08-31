# Output Resolution and Conflicts

## Resolution Hierarchy
The system supports resolving the exact deliverable expected by a task through an inheritance hierarchy:
`Task > Pipeline > Stage > Team`

The `OutputContractResolver` aggregates and merges these contracts sequentially from lowest specific priority to highest specific priority.

## Contract Merging
The `OutputContractMerger` applies overrides (e.g., overriding a pipeline's general video requirement with a task's specific 4K requirement).
- Specific requirements override general ones only when they are compatible.
- Conflicting requirements (e.g., base formats `["webm"]` and override formats `["mp4"]`) raise an `OutputContractConflict`. They do not silently override.
