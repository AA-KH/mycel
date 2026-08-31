# Team Tool Model

## The `ToolDefinition` Entity (Global)
Owned by the `tools` domain, this represents the execution definition.
- **`id`**: Stable string identifier (e.g. `web.search`).
- **`category`**: E.g., `research`, `filesystem`, `media`.
- **`risk_level`**: `low`, `medium`, `high`, `critical`.
- **`enabled`**: Lifecycle toggle.

## The `TeamToolAssignment` Entity
Owned by the `tools/team` domain, mapping tools to organizational units.
- **`team_id`**: Reference to the Organization/Team.
- **`tool_id`**: Reference to the Global ToolRegistry.
- **`required`**: Boolean indicating necessity.
- **`importance`**: `CORE`, `SUPPORTING`, `OPTIONAL`.
- **`access_mode`**: `READ`, `WRITE`, `EXECUTE`, `FULL`.
- **`status`**: `ACTIVE`, `INACTIVE`.

## Tool Lifecycle
- **Tool Status**: The global tool uses `enabled: bool`.
- **Assignment Status**: Uses soft-lifecycles (`ACTIVE`, `INACTIVE`). When a tool is removed from a team, the assignment is marked inactive to preserve historical agent task logs.

## Team Tool Availability
A Team is only considered to have access to a tool if:
1. The `TeamToolAssignment` exists and is `ACTIVE`.
2. The global `ToolDefinition` exists and is `enabled=True`.
