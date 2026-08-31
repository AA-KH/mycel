# Phase 10: Task Orchestration System

## Purpose
The **Task Orchestration System** transforms raw natural language **User Requests** into structured, validated, versioned **TaskPlans**.

It answers: **"What work needs to happen?"**
It does **NOT** answer:
- *"Which employee should do it?"* (Belongs to Smart Hiring)
- *"How does the Agent execute it?"* (Belongs to Agent Runtime)

---

## Final Responsibility Boundaries

| System | Primary Question / Responsibility |
|---|---|
| **Task Orchestrator** | TASK → VALIDATED EXECUTION PLAN |
| **Team Capability Resolver** | TEAM → CAPABILITY MATRIX |
| **Team Operating System** | TEAM → OPERATIONAL CONFIGURATION |
| **Hiring System** | WORK UNIT → EMPLOYEE SELECTION |
| **Agent Runtime** | EMPLOYEE → AGENT INSTANTIATION & RUNTIME |
| **Tools Subsystem** | AGENT → TOOL ACTION |
| **Artifact System** | ACTION → PHYSICAL DELIVERABLE |
| **Quality Gates** | DELIVERABLE → VALIDATION |

---

## Architectural Flow

```
USER REQUEST
   │
   ▼
TaskAnalyzer (Request Normalization, Intent & Outcome Extraction)
   │
   ▼
CapabilityRequirementResolver (Required Capabilities Resolution)
   │
   ▼
TeamResolver (Candidate Team & Contract Resolution via Team OS)
   │
   ▼
TaskDecomposer (WorkUnit Breakdown per Team)
   │
   ▼
DependencyBuilder & CycleDetector (DAG Construction & Cycle Validation)
   │
   ▼
TaskPlanner (Versioned TaskPlan Assembly)
   │
   ▼
TaskPlanValidator (Deterministic Registry Validation)
   │
   ▼
TASK PLAN (READY_FOR_EXECUTION / WAITING_FOR_INPUT / BLOCKED)
```

---

## Key Rules & Constraints
1. **Planning vs Execution**: Task Orchestration produces a `TaskPlan` stopping at `READY_FOR_EXECUTION`. No execution of LLM code, pipelines, tools, artifacts, quality gates, or Cloudinary uploads occurs in Phase 10.
2. **Deterministic Registry Validation**: LLM proposals are UNTRUSTED. Every team, pipeline, execution contract, output contract, and collaboration contract is strictly validated against system registries.
3. **Work Unit Principle**: 1 WorkUnit = 1 coherent piece of work owned by EXACTLY 1 team. No micro-actions (e.g. "click button", "search google").
4. **Plan Immutability & Versioning**: Approved plans are immutable. Material changes produce a new plan version (`v1`, `v2`).
