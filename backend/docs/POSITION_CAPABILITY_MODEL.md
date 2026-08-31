# Position Capability Model

The Capability Model in Mycel is hierarchical and cumulative. The Effective Capability of a Team Member is determined by the intersection and summation of the Team, the Position, and the Individual.

## The Resolution Formula

```text
Team Common Capabilities
  + Position Capabilities
  ================================
  = Effective Position Capability
```

### Team Common Capabilities
These are universally required for every member of the Team.
- *Example (Creative Team):* `storytelling`, `creative_direction`, `file_storage`

### Position Specific Capabilities
These are specialized requirements layered on top of the Team baseline.
- *Example (Video Editor):* `video_editing`, `motion_graphics`, `ffmpeg`

### Effective Position Capability
This represents the strict operational floor that any candidate must meet.
- *Effective (Video Editor):* `storytelling`, `creative_direction`, `file_storage`, `video_editing`, `motion_graphics`, `ffmpeg`

## Enforcement Rules

1. **Non-Weaken Rule:** A Position may *tighten* (raise the required minimum proficiency) or *add* to Team capabilities, but it **cannot weaken** or mark a mandatory Team capability as optional. If it attempts to, the `PositionValidator` will reject the definition.
2. **References Only:** The model relies purely on referencing stable `skill_id`, `tool_id`, and `knowledge_id` identifiers from the global Registries.
