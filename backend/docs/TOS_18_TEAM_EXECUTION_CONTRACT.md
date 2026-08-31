# TOS 18: Team Execution Contract

## Purpose

The **Team Execution Contract** is the formal, versioned agreement that defines how a Team accepts, processes, and delivers a specific type of work.

It answers:

> "Given this Team and this task type, what inputs are required, what capabilities are needed, which pipeline runs, what output is expected, and what does done look like?"

It does **not** execute anything.

---

## Architectural Position

```
TASK
  ↓
TEAM CAPABILITY RESOLVER  (TOS 15)
  ↓
TEAM                       (TOS 1–13)
  ↓
TEAM EXECUTION CONTRACT    ← TOS 18
  ↓
PIPELINE                   (TOS 6–7)
  ↓
POSITION + HIRING          (TOS 10, future)
  ↓
MEMBER → AGENT → RUNTIME   (future)
```

---

## Contract Model

| Field | Description |
|---|---|
| `contract_id` | Stable ID e.g. `creative.promotional_video.v1` |
| `team_id` | Owning team — must exist in TeamRegistry |
| `version` | Integer version number |
| `status` | `DRAFT` / `ACTIVE` / `DEPRECATED` / `ARCHIVED` |
| `accepted_task_types` | List of task type strings this contract handles |
| `required_inputs` | Inputs the task must supply |
| `optional_inputs` | Inputs accepted but not required |
| `required_skills` | Skill IDs from team capabilities |
| `required_tools` | Tool IDs from team capabilities |
| `required_knowledge` | Knowledge space IDs |
| `reasoning_profile` | Reasoning profile ID |
| `pipeline_id` | Must belong to the same team |
| `stage_expectations` | Lightweight expected stage outcomes |
| `output_contract_ids` | References to existing OutputContracts |
| `expected_artifacts` | Expected physical deliverables |
| `quality_gate_ids` | Quality gates to apply — executed by Quality System |
| `completion_criteria` | List of criteria that define "done" |
| `failure_conditions` | Enum list of recognised failure modes |
| `execution_constraints` | max_tool_calls, human_approval, etc. |
| `handoff_contract` | What is passed to the next system |

---

## Validation Layers

1. **Identity** — `contract_id` and `team_id` present
2. **Team Ownership** — `team_id` exists in `TeamRegistry`
3. **Pipeline Ownership** — `pipeline_id` exists and belongs to `team_id`
4. **Capabilities** — required skills/tools resolved via `TeamCapabilityResolver`
5. **Task Types** — at least one `accepted_task_types` entry
6. **Completion Criteria** — non-empty
7. **Failure Conditions** — non-empty
8. **Inputs / Status** — warnings for missing inputs or DRAFT status

## Non-Goals

- Does NOT execute pipelines
- Does NOT call LLMs
- Does NOT invoke tools
- Does NOT select members
- Does NOT route tasks
- Does NOT generate artifacts
- Does NOT upload to Cloudinary
- Does NOT perform hiring
