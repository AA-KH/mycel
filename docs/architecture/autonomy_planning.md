# Autonomy Planning

The planning subsystem converts a high-level `CompanyObjective` into an executable Directed Acyclic Graph (DAG) of tasks. 

## The Company Plan

A `CompanyPlan` is versioned. When an objective encounters a failure or requirement change, a NEW plan version is created via the `ReplanningEngine`, and the old plan is marked `SUPERSEDED`. History is never overwritten.

A plan consists of:
1.  **Milestones:** Groupings of tasks that represent major phases (e.g., Research, Design, Build).
2.  **TaskRequestDescriptors:** Templates for tasks that need to be executed.
3.  **Dependency Graph:** Edges indicating which descriptors must complete before others can start.
4.  **Critical Path:** Computed using a topological sort, representing the longest path through the graph.

## Planner

The `ObjectivePlanner` is strictly deterministic for Phase 16. It uses a predefined taxonomy of phases:
`Research → Design → Build → Test → Deploy → Evaluate`

In future phases, this can be replaced by an LLM-driven planner, but the output must always be a structured `CompanyPlan` that passes validation.

## Plan Validator

Before a plan can be executed (or even attached to an objective), it must pass the `PlanValidator`. 
The validator checks for:
*   Cycles in the dependency graph (DAG validation).
*   Budget feasibility (does estimated cost exceed available budget?).
*   Deadline feasibility.
*   Structural correctness (empty milestones, missing references).
