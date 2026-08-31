# Team Operating System Boundaries

Clear ownership boundaries for every concept in Mycel.

---

## Boundary Map

| Concept | Owner | Boundary |
|---|---|---|
| **Organization** | `organization/company/` | Who owns the company? |
| **Department** | `organization/departments/` | How is the company organized? |
| **Team** | `teams/<team_id>/` | Who performs a category of work? |
| **Common Skills** | `teams/<team_id>/common/skills/` | What skills does the whole team share? |
| **Common Tools** | `teams/<team_id>/common/tools/` | What tools does the whole team use? |
| **Knowledge** | `teams/<team_id>/common/knowledge/` | What information does the team have? |
| **Reasoning** | `teams/<team_id>/common/reasoning/` | How should the team approach problems? |
| **Pipeline** | `teams/<team_id>/pipelines/` | How does the team approach work? |
| **Pipeline Stage** | Inside pipeline definitions | What step is being performed? |
| **Quality Gate** | `quality/` | Is the work acceptable? |
| **Output Contract** | `outputs/` | What must be produced? |
| **Artifact** | `artifacts/` | What was physically produced? |
| **Position** | `teams/<team_id>/positions/` | What role exists inside a team? |
| **Member** | `teams/<team_id>/team_members/` | Who occupies a position? |
| **Workforce** | `workforce/` | Who can work across the organisation? |
| **Capability Inheritance** | `teams/capabilities/` | How do members inherit team capabilities? |
| **Execution Contract** | `execution/contracts/` | How does a team execute a task type? |
| **Collaboration Contract** | `execution/collaboration/` | How does one team request work from another? |
| **Agent** | `agents/` | Runtime identity of a member |
| **Runtime** | `agents/runtime/` | How does the agent execute? |
| **Reasoning Engine** | `execution/reasoning/` | How does the agent think? |
| **Tool** | `tools/` | What actions can the agent perform? |
| **LLM** | `execution/llm/` | Language model integration |
| **Team Registry** | `teams/registry.py` | Which teams exist? |
| **Pipeline Registry** | `execution/pipelines/registry.py` | Which pipelines exist? |
| **Capability Resolver** | `teams/resolver.py` | What can a team do? |
| **Team Validator** | `teams/validator.py` | Is a team validly configured? |
| **Execution Contract Registry** | `execution/contracts/registry.py` | Which execution contracts exist? |
| **Collaboration Registry** | `execution/collaboration/registry.py` | Which collaboration contracts exist? |
| **Team Operating System** | `teams/tos/` | How do all team-level components fit together? (TOS 20) |
| **Task Router** | FUTURE | Which team should handle the task? |
| **Smart Hiring** | FUTURE | Which member should perform the work? |

---

## Cross-Boundary Rules

| Rule | Detail |
|---|---|
| Teams do not access each other's internals | Use `TeamCollaborationContract` |
| Members do not directly invoke tools | Tools are invoked via Agent Runtime |
| Snapshots contain IDs only | Never embed live objects or secrets |
| Execution contracts do not execute | They are contract definitions only |
| Collaboration contracts do not orchestrate | They define the relationship only |
| Team Operating System is read-only | All mutation goes through owning subsystem |
| No two subsystems maintain the same data | Single source of truth enforced by design |

---

## What Each Boundary Does NOT Own

| Concept | Does NOT own |
|---|---|
| Team | Member personal data beyond IDs |
| Execution Contract | Pipeline execution logic |
| Collaboration Contract | Cross-team messaging or transport |
| Team Operating System | Any data — it only aggregates references |
| Agent | Team configuration — Agent reads from TOS |
| Task Router | Team capability definitions |
| Smart Hiring | Team pipeline logic |
