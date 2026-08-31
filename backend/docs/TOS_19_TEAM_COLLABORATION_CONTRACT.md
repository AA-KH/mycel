# TOS 19: Team Collaboration Contract

## Purpose

The **Team Collaboration Contract** defines the formal, versioned agreement governing how one Team requests and receives work from another.

It answers:

> "Given Team A (requester) and Team B (provider), what inputs are needed, what capabilities must B have, which pipeline runs, what output is expected, and what does successful handoff look like?"

It does **not** execute anything.

---

## Architectural Position

```
TASK
  ↓
TEAM CAPABILITY RESOLVER
  ↓
TEAM
  ↓
EXECUTION CONTRACT         (TOS 18)
  ↓
PIPELINE
  ↓
TEAM COLLABORATION CONTRACT  ← TOS 19
  ↓
PROVIDER TEAM
  ↓
PROVIDER EXECUTION CONTRACT
  ↓
PROVIDER PIPELINE → MEMBER → AGENT → RUNTIME
```

---

## Key Principles

| Principle | Rule |
|---|---|
| No self-collaboration | `requesting_team_id ≠ providing_team_id` |
| No auto-selection | Provider is declared, not chosen |
| Isolation | Requester never accesses provider's members, tools, prompts, or knowledge directly |
| Immutability | ACTIVE contracts are immutable; create a new version to change |
| Determinism | Same triple (requesting, providing, request_type) → same ACTIVE contract |

---

## Contract Model

| Field | Description |
|---|---|
| `contract_id` | Stable ID e.g. `research_to_developer.requirements.v1` |
| `requesting_team_id` | Team requesting the work |
| `providing_team_id` | Team performing the work |
| `request_type` | Request classification |
| `accepted_request_types` | List of types this contract handles |
| `required_inputs` | Inputs from requester to provider |
| `required_capabilities` | Provider capabilities required |
| `execution_contract_id` | Provider's execution contract (optional) |
| `pipeline_id` | Provider's pipeline (optional) |
| `required_output_contract_ids` | Expected outputs |
| `quality_gate_ids` | Quality requirements |
| `sequence_type` | SEQUENTIAL / PARALLEL / CONDITIONAL |
| `completion_criteria` | When collaboration is done |
| `failure_conditions` | Recognised failure modes |
| `collaboration_constraints` | max_round_trips, human_approval, etc. |
| `handoff_contract` | What provider hands back to requester |

---

## Validation Layers (11)

1. Identity checks
2. Requesting team exists in TeamRegistry
3. Providing team exists in TeamRegistry
4. Self-collaboration guard
5. Execution contract reference (team ownership)
6. Pipeline reference (team ownership)
7. Provider capability compatibility
8. Request types non-empty
9. Completion criteria non-empty
10. Failure conditions non-empty
11. Inputs / status warnings

## Non-Goals

- Does NOT execute pipelines
- Does NOT call LLMs
- Does NOT invoke tools
- Does NOT select provider teams
- Does NOT route tasks
- Does NOT generate artifacts
- Does NOT upload to Cloudinary
- Does NOT perform hiring
- Does NOT implement messaging transport
