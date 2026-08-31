# Collaboration Security Model

## Default Deny Policy
Collaboration between two teams is strictly prohibited unless an active `TeamCollaborationContract` (TOS 19) explicitly allows it.
Attempts to initiate a handoff without an active contract are rejected with `CONTRACT_INVALID`.

## Isolation Invariants
1. **Team Isolation**: Producing team internal tools, knowledge spaces, and employee profiles are NOT shared with the receiving team.
2. **Tool Isolation**: Receiving teams do NOT inherit the tools of the producing team.
3. **Credential Isolation**: Secrets (`api_key`, `secret`, `password`, `token`, `credentials`) are stripped from payloads by `HandoffValidator` and `CollaborationContextBuilder`.
4. **No Hidden Reasoning**: Chain-of-thought (`think`, `reasoning_trace`) is stripped and prohibited.
5. **No Direct Invocations**: Direct agent-to-agent method calls are not supported. Communication must occur through `CollaborationService` handoffs.
