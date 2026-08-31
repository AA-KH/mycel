# Team Validation Rules

Mycel strictly enforces the following validation layers over its 7 core Teams:

## Layer 1: Identity
- `team_id` must exist and match canonical identifiers.
- `display_name` must be set.

## Layer 2: Registry Integration
- Discovered Teams must successfully register with the `TeamRegistry`.

## Layer 3: Pipelines
- A Team must possess at least 1 pipeline.
- Pipelines mapped to a Team must declare that Team explicitly via `team_id` (Pipeline Ownership Validation).
- Discovered pipelines must successfully register with the `PipelineRegistry`.

## Layer 4: Workforce & Position Alignment
- A Team must possess a minimum of 3 Baseline Members.
- A Member must explicitly declare the `team_id` of the Team it belongs to.
- A Member must declare a `position_id`.

## Layer 5: Inheritance Isolation
- Members can declare individual specializations.
- The `TeamCapabilityResolver` verifies that these specializations do not artificially ascend into the Team's `common_skills` capabilities.

## Error Codes
- `TEAM_ID_REQUIRED`: Missing team definition identity.
- `TEAM_NAME_REQUIRED`: Missing display name.
- `REGISTRY_DISCOVERY_FAILED`: Registries failed to index the provided object.
- `PIPELINE_NOT_FOUND`: Empty workflow configuration.
- `PIPELINE_TEAM_MISMATCH`: Pipeline explicitly assigned to conflicting team.
- `MEMBER_COUNT_INVALID`: Falls below minimum baseline threshold.
- `MEMBER_TEAM_MISMATCH`: Member explicitly assigned to conflicting team.
- `POSITION_NOT_FOUND`: Member lacks a role.
- `CAPABILITY_RESOLUTION_FAILED`: Capabilities failed structural resolution logic.
