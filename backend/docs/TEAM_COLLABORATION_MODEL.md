# Team Collaboration Model

## How Teams Collaborate

Teams in Mycel are autonomous. They do not directly access each other's internal members, reasoning, tools, knowledge, or runtime state.

All inter-team work is governed by a **TeamCollaborationContract**.

```
Requesting Team
      │
      │  (declares input, references contract)
      ▼
TeamCollaborationContract
      │
      │  (specifies what provider must deliver)
      ▼
Providing Team
      │
      │  (executes internally using its own pipeline)
      ▼
Output / ArtifactReference
      │
      │  (handoff back to requester)
      ▼
Requesting Team continues its work
```

## How ArtifactReference Works

When the providing team produces a physical deliverable (video, document, code), it is NOT transferred as raw binary. Instead:

1. Providing team runs its pipeline.
2. Artifact System stores the result (e.g. Cloudinary for media).
3. An `ArtifactReference` (ID + URI + type) is returned.
4. The collaboration handoff contains only the `ArtifactReference`.
5. Requesting team uses the reference to retrieve or display the artifact.

This keeps team boundaries clean and avoids binary coupling.

## How Private Capabilities Stay Isolated

| Asset | Shared? | Mechanism |
|---|---|---|
| Private knowledge | No | Provider outputs a document/report; requester receives ArtifactReference |
| Private tools | No | Provider executes tools; requester receives the result |
| Reasoning traces | No | Only reasoning summary may be shared if explicitly declared |
| Member identities | No | Collaboration contract references positions, not individual members |
| Agent state | No | Agent runtime is internal to the providing team |

## Sequence Types

| Type | Meaning |
|---|---|
| SEQUENTIAL | Provider must complete before requester proceeds |
| PARALLEL | Provider and requester may work concurrently |
| CONDITIONAL | Collaboration only occurs if a declared condition is met |
