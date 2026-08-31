# TOS 20: Team Operating System Integration

## Purpose

TOS 20 is the **integration phase** for the entire Team Operating System. It provides a unified, read-only view over all TOS 0–19 subsystems through a clean facade.

It answers:

> "Given a Team ID, what is this team, what can it do, how does it work, what does it produce, how does it validate work, how does it execute, and how does it collaborate?"

**Nothing executes. Nothing is mutated. No new source of truth is created.**

---

## Architecture

```
teams/tos/
    models.py     ← Snapshot, HealthReport, ValidationReport, CapabilityView,
                    OperatingProfile, ContractMap, TOSTeamReadiness
    context.py    ← TeamExecutionContext (immutable)
    service.py    ← TeamOperatingSystemService (read-only facade)
```

---

## TeamOperatingSystemService

The facade. Accepts all registries via dependency injection.

| Method | Returns | Description |
|---|---|---|
| `get_team_snapshot(team_id)` | `TOSTeamSnapshot` | Lightweight snapshot — IDs and safe metadata only |
| `get_operating_profile(team_id)` | `TOSTeamOperatingProfile` | Human-readable derived profile |
| `get_team_health(team_id)` | `TOSTeamHealthReport` | Health summary from validation results |
| `get_validation_report(team_id)` | `TOSTeamValidationReport` | Aggregated validation across all subsystems |
| `get_capability_view(team_id)` | `TOSTeamCapabilityView` | Derived capability view from TeamCapabilityResolver |
| `get_execution_contracts(team_id)` | `List[str]` | Active execution contract IDs |
| `get_collaboration_contracts(team_id)` | `TOSContractMap` | Incoming + outgoing collaboration IDs |
| `make_execution_context(...)` | `TeamExecutionContext` | Immutable execution identity context |
| `list_all_team_ids()` | `List[str]` | All registered team IDs |

---

## TOSTeamReadiness (TOS 20 extension)

| State | Meaning |
|---|---|
| `READY` | All components valid, no errors |
| `PARTIALLY_READY` | Identity valid but ≥1 non-critical capability missing |
| `DEGRADED` | Previously operational; critical runtime dependency unavailable |
| `NOT_READY` | Fundamental identity or configuration broken |

---

## Validation Aggregation (11 layers)

Calls existing validators — no duplicate logic:

1. Identity (TeamRegistry lookup)
2. Capabilities (TeamCapabilityResolver)
3. Pipelines (PipelineRegistry + cross-team ownership check)
4. Execution Contracts (ExecutionContractRegistry + team ownership)
5. Collaboration Contracts (TeamCollaborationContractRegistry + ownership)
6. Full team validation (existing TeamValidator from TOS 17)

---

## Security Boundaries

`TOSTeamSnapshot` never contains:
- API keys or credentials
- Private prompts or reasoning traces
- Raw knowledge documents
- Raw artifact binaries
- Personal employee data beyond IDs

Only IDs, references, counts, and safe summaries are included.

---

## Non-Goals

- Does NOT execute pipelines
- Does NOT call LLMs
- Does NOT invoke tools
- Does NOT create agents
- Does NOT generate artifacts
- Does NOT hire members
- Does NOT route tasks
- Does NOT mutate any subsystem
- Does NOT create a second source of truth
- Does NOT become a god object
