# Collaboration Protocol Reference (v1.0)

## Message Protocol (`CollaborationMessage`)
- `protocol_version`: `"1.0"`
- `message_id`: str (e.g. `msg_a1b2c3d4`)
- `session_id`: str
- `task_id`: str
- `source_work_unit_id`: str
- `target_work_unit_id`: str
- `message_type`: MessageType (`REQUEST`, `RESPONSE`, `HANDOFF`, `STATUS`, `ERROR`, `APPROVAL_REQUEST`, `APPROVAL_RESULT`)
- `payload`: Dict[str, Any] (Structured JSON only, no arbitrary prose)
- `artifact_references`: List[ArtifactReference]

## Handoff Protocol (`CollaborationHandoff`)
- `handoff_id`: str
- `session_id`: str
- `source_work_unit_id`: str
- `target_work_unit_id`: str
- `contract_id`: str
- `input_references`: List[str]
- `output_references`: List[str]
- `payload`: Dict[str, Any]
- `artifact_references`: List[ArtifactReference]
- `status`: HandoffAckStatus (`ACCEPTED`, `REJECTED`, `NEEDS_CLARIFICATION`, `BLOCKED`)

## Clarification Protocol (`CollaborationClarification`)
- `clarification_id`: str
- `session_id`: str
- `question`: str
- `required_input`: str
- `reason`: str
- `status`: ClarificationSessionStatus (`PENDING`, `RESOLVED`, `EXPIRED`)
- `response_payload`: Optional[Dict[str, Any]]
