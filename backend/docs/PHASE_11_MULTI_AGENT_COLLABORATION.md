# Phase 11: Multi-Agent Collaboration System

## Purpose
The **Multi-Agent Collaboration System** provides controlled, contract-governed, artifact-referenced, and minimal-context communication between Teams and Agents across Work Units.

It replaces unrestricted agent-to-agent chat swarms with **explicit, contract-driven handoffs**.

---

## Architectural Principles & Invariants
1. **Default Deny**: No active `TeamCollaborationContract` = No Collaboration.
2. **Controlled Handoffs**: Communication happens exclusively through structured `CollaborationHandoff` payloads and `ArtifactReference` IDs.
3. **Minimal Context Projection**: `CollaborationContextBuilder` prunes context to include ONLY required inputs, relevant constraints, and artifact references. Excludes chain-of-thought, internal team tools, full chat history, and credentials.
4. **Loop & Cycle Protection**: Enforces `max_handoffs` (default 5) and `max_clarifications` (default 2) per session. Exceeding limits transitions status to `BLOCKED`.
5. **No Execution Side Effects**: No employee hiring, no agent runtime instantiation, no tool calls, no LLM code execution, no binary artifact creation, no Cloudinary uploads.

---

## Subsystem Flow

```
WorkUnit A (Producer)
   │
   ▼
Produces Output / ArtifactReference
   │
   ▼
CollaborationRouter (Resolves target WorkUnit B, verifies TeamCollaborationContract TOS 19)
   │
   ▼
CollaborationService.request_collaboration() -> Creates CollaborationSession (CREATED)
   │
   ▼
HandoffValidator (Validates source/target teams, contract compatibility, required inputs, schema, artifacts)
   │
   ▼
CollaborationHandoff (Structured payload + ArtifactReferences, status = HANDOFF_VALIDATED)
   │
   ▼
CollaborationContextBuilder (Constructs minimal CollaborationContext for WorkUnit B)
   │
   ▼
Delivery & Acknowledgement (ACCEPTED / REJECTED / NEEDS_CLARIFICATION)
   │
   ▼
CollaborationSession (COMPLETED / BLOCKED)
```
