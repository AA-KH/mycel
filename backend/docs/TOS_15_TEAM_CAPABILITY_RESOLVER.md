# TOS 15: Team Capability Resolver

The `TeamCapabilityResolver` determines the effective capabilities of a Team by answering the critical question: *"What can this Team actually handle?"*

It unifies the disparate properties of a Team (skills, tools, pipelines, outputs, positions) into a normalized `TeamCapabilityProfile`.

## Responsibilities
- Merge `TeamRegistry` properties (skills, tools, positions) into the profile.
- Traverse the `PipelineRegistry` to resolve pipeline-owned properties (stages, output contracts, quality constraints) for the specified team.
- Ensure strict isolation: A team is only granted capabilities explicitly declared or owned by it.
- Produce a unified `TeamCapabilityResolutionResult`.
- Provide matching primitives for future task routing (e.g., `matches_requirements(team_id, requirements)`).

## Non-Responsibilities (Strict Boundaries)
- **Execution:** It does *not* execute tools, run pipelines, or invoke agents.
- **Hiring:** It does *not* instantiate Members or perform candidate ranking.
- **Inflation:** It does *not* look at individual members and inflate the Team's core capabilities with their personal specializations. 

## Resolution Modes
- **Lenient Mode (Default):** The resolver creates the profile to the best of its ability. Invalid capability references are pushed to the `warnings` list.
- **Strict Mode:** If any dependency or core reference is broken, the resolver bails immediately, reporting `resolved=False` and appending to the `errors` list.
