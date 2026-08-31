# Skill Model

## The `Skill` Entity
The global definition of a capability.
- **`skill_id`**: A stable, machine-readable string (e.g. `software_development`).
- **`name`**: Internal identifier.
- **`display_name`**: Human-readable name.
- **`domain`**: The overarching domain (e.g., `engineering`, `legal`, `shared`).
- **`category`**: A high-level categorization (e.g. `technical`, `analytical`, `communication`).

## The `TeamSkillAssignment` Entity
The association mapping a globally defined `Skill` to a specific `Team`.
- **`team_id`**: The team this assignment belongs to.
- **`skill_id`**: The referenced capability.
- **`proficiency_baseline`**: The expected minimum capability level (0-100).
- **`importance`**: How critical the skill is.
- **`required`**: Whether the skill is strictly mandatory for the team's operational survival.

## Skill Lifecycle
Skills and assignments use soft-lifecycles to prevent breaking historical data.
- **Skill Status**: `DRAFT`, `ACTIVE`, `DEPRECATED`, `ARCHIVED`.
- **Assignment Status**: `ACTIVE`, `INACTIVE`.
Rather than physically deleting a skill when it is no longer needed by a team, the `TeamSkillAssignment` status is simply transitioned to `INACTIVE`.

## Categories & Domains
- **Categories**: Bound by the `SkillCategory` enum (`technical`, `research`, `analytical`, `creative`, `communication`, `legal`, `business`, `operational`, `management`, `security`, `quality`, `other`).
- **Domains**: Free-text strings defining logical groupings (e.g. `engineering`, `research`, `creative`).
