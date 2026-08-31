# Phase TOS 15 Report: Team Capability Resolver

## Implementation Summary
Phase TOS 15 implemented the **Team Capability Resolver**. This architectural component deterministically aggregates scattered Team definitions (Skills, Tools, Pipelines, Positions) into a normalized `TeamCapabilityProfile`. It answers the core question: *"What can this Team handle?"* without crossing into the execution boundary.

## Resolver Architecture
- **Location:** `teams/resolver.py`
- **Dependency Injection:** Relies dynamically on `TeamRegistry` (TOS 13) and `PipelineRegistry` (TOS 14).
- **Models:** Built `TeamCapabilityProfile` to house normalized strings/references of operational boundaries. Built `TeamCapabilityResolutionResult` to handle graceful failures and warnings.

## Resolution Rules & Validations
- **No Member Inflation:** Verified that Team capabilities are strictly scoped to explicit team definitions and pipelines, completely isolated from specific member specializations.
- **Strict/Lenient Modes:** Implemented failure states based on the `strict` boolean parameter, allowing for robust upstream error handling.
- **Matching Primitive:** Developed `matches_requirements()`, comparing a dictionary of requirements against the resolved capability arrays.

## Boundary Adherence
Tests verify that the `TeamCapabilityResolver`:
- Does not instantiate agents or call LLMs.
- Does not generate artifacts.
- Does not hire or evaluate specific members.

## Files Created/Modified
- **Created**: `teams/capabilities/models.py`
- **Created**: `teams/resolver.py`
- **Created**: `tests/teams/test_team_resolver.py`
- **Created**: `docs/TOS_15_TEAM_CAPABILITY_RESOLVER.md`
- **Created**: `docs/TEAM_CAPABILITY_MODEL.md`
- **Created**: `docs/TEAM_CAPABILITY_RESOLUTION.md`
- **Created**: `docs/PHASE_TOS_15_REPORT.md`

## Future Integration Points
- **Task Routing:** The `matches_requirements()` primitive is exactly the hook the Task Router needs. By feeding Task requirements to the resolver, the router can securely determine the correct Team.
- **Smart Hiring:** The resulting Profile allows the Hiring Engine to understand the macro-requirements of a team before drilling down into Position definitions.

**PHASE TOS 15 IS COMPLETE.**
