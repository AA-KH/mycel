# TOS 17: Team Validation

The Team Validator ensures Mycel operates securely, reliably, and consistently by continuously auditing the Team Seed Catalogue and its interaction with the broader Registry architecture.

## Responsibilities
- Validate the core structural definitions (identity, skills, tools) of each team.
- Ensure cross-system references match (pipelines map to teams, members map to positions, positions map to teams).
- Ensure explicit isolation: Team boundaries are impenetrable to unintentional capability bleeding.

## Strict Boundaries
- **No Agent/LLM invocation:** The validator evaluates configurations, not intelligent agent execution.
- **No Environment mutation:** Validation verifies existence of pipelines and contracts but never attempts artifact generation or quality gate triggering.
- **Stateless Execution:** Validation can be run thousands of times safely and identically.

## Modes
Validation runs either leniently (which allows Teams with missing non-critical parameters to pass as `READY_WITH_WARNINGS`), or via **strict mode** (`strict=True`), where warnings automatically force the Team into a `NOT_READY` state.
