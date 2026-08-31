# Hiring Migration

## Legacy Manager Agent Flow
Prior to Phase 9, the `ManagerAgent` orchestrated tasks using a simple LLM map-reduce strategy:
1. `ManagerAgent` analyzed a task.
2. It produced a JSON list of subtasks, assigning each to a string `team` (e.g. "ui-designer", "backend-architect").
3. `build_team_agent(team)` instantiated a `GenericAgent` with a dynamically generated system prompt containing that team name.

This completely bypassed the Employee system and relied on unstructured, non-deterministic agents.

## Phase 9 Smart Hiring Integration
The `ManagerAgent` has now been migrated to use the deterministic `HiringEngine`.

1. `ManagerAgent` still produces a JSON list of subtasks.
2. For each subtask, the `ManagerAgent` calls `hiring_engine.select_candidate(subtask_desc)`.
3. The `HiringEngine` uses the LLM via `HiringRequirementBuilder` to parse the subtask into deterministic `HiringRequirement` objects.
4. Candidates are filtered and scored mathematically.
5. If a candidate is selected, `ManagerAgent` fetches the *actual* employee identity (e.g. "Aarav Mehta, Research Specialist").
6. The runtime instantiated to execute the subtask is now given the identity and reasoning profile of the chosen employee.

## Fallback Mechanism
To ensure system stability during this transition (and for any subtasks so abstract that no candidate qualifies under hard requirements), the `ManagerAgent` retains a graceful fallback:
If the `HiringEngine` returns a `NO_CANDIDATE` status, the system falls back to `build_team_agent(team)` to spawn the legacy generic agent. This ensures tests and legacy API clients do not break while the workforce catalogue is built out in future phases.
