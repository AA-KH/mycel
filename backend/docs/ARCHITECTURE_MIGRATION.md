# Architecture Migration Map

This document tracks legacy modules that currently violate the clean architectural boundaries defined in TOS 0, and outlines their migration targets.

## `backend/agents/manager_agent.py`
*   **Current Responsibility:** Planning, task breakdown, execution orchestration, and employee/team delegation.
*   **Target Boundary:** Should solely be a high-level `Agent` orchestration construct; team pipelines and hiring systems should own task routing.
*   **Migration Priority:** Medium (partially migrated in Phase 9 via `HiringEngine`).
*   **Risk:** High. Removing it prematurely will break end-to-end task flows.
*   **Status:** DEPRECATED (Bridged). Awaiting TOS Team Pipeline implementation to replace its orchestration duties.

## `backend/agents/team_agents.py`
*   **Current Responsibility:** Hardcoded generic agent roles (e.g. `ResearchAgent`, `DeveloperAgent`) that bundle role, identity, and system prompt logic.
*   **Target Boundary:** Should be entirely replaced by the dynamic `Workforce` system (`Employee` -> `AgentSnapshot`).
*   **Migration Priority:** High.
*   **Risk:** Medium. Currently acts as a safe fallback when `HiringEngine` fails to find a specialized employee.
*   **Status:** DEPRECATED. Slated for removal once the employee catalogue fully supports all required domains.

## `backend/agents/legacy_adapter.py`
*   **Current Responsibility:** Translates Phase 8/9 Employee definitions into legacy `BaseAgent` structures and mock implementations of the `AgentRuntime`.
*   **Target Boundary:** Will be absorbed directly into the `AgentRuntime` lifecycle initialization.
*   **Migration Priority:** Low.
*   **Risk:** Low. Only used as a compat layer.
*   **Status:** DEPRECATED.

## `backend/agents/base_agent.py`
*   **Current Responsibility:** Base class for all legacy monolithic agents. Directly manages LLM message history and parsing instead of relying on `ReasoningEngine` and `AgentRuntime`.
*   **Target Boundary:** Completely obsolete once `AgentRuntime` fully takes over execution lifecycles.
*   **Migration Priority:** High.
*   **Risk:** High. All legacy systems depend on it.
*   **Status:** DEPRECATED.
