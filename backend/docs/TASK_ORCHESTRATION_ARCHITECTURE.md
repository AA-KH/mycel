# Task Orchestration Architecture

```
USER REQUEST
 ↓
TASK (Task Entity, original & normalized request)
 ↓
OUTCOME (Objective, requested outputs, success definition)
 ↓
CAPABILITIES (TaskCapabilityRequirement mapping)
 ↓
TEAMS (Candidate Team & Contract Resolution)
 ↓
WORK UNITS (Single-team cohesive work units)
 ↓
DEPENDENCIES (WorkUnitDependency DAG, cycle detection)
 ↓
PLAN (Versioned TaskPlan v1)
 ↓
VALIDATION (Deterministic Team, Contract, Pipeline, Output validation)
 ↓
READY FOR EXECUTION (TaskPlan ready for future Execution Orchestrator & Hiring)
```

## Architectural Isolation
- **No God Objects**: Modular separation into `TaskAnalyzer`, `TaskDecomposer`, `CapabilityRequirementResolver`, `TeamResolver`, `TaskPlanner`, `TaskPlanValidator`, `DependencyValidator`, and `TaskOrchestrator`.
- **Cross-Team Collaboration Integration**: Cross-team WorkUnit dependencies require registered `TeamCollaborationContract` references (TOS 19).
- **Prompt Injection Defense**: Sanitizes raw input without destroying meaning. Validates all resolved entities deterministically.
