# Capability Provenance

## Why Provenance Exists
In an autonomous operating system, "Why can this Agent do this?" is a critical question. If an Agent accidentally mutates a production database, administrators must be able to trace exactly where that capability was granted. 

Provenance solves the "Black Box" problem of inherited access by tracking the exact origin of every capability down to the specific file and abstraction layer.

## The Provenance Model
Every `ResolvedCapability` contains a `CapabilityProvenance` object:
```json
{
  "capability_id": "programming",
  "capability_type": "skill",
  "source_type": "specialization",
  "source_id": "emp_kabir",
  "inherited_from": "dev_be_baseline",
  "reason": "Updated by specialization"
}
```

## Explainability Tracing
If an administrator questions why Kabir possesses advanced programming skills:
1. The resolver logs show the capability exists at proficiency 85.
2. The `source_type` reveals it came from `specialization` (Kabir's personal file).
3. But tracing the inheritance tree backward (`inherited_from` -> `dev_be_baseline` -> `backend_engineer` -> `developer`) reveals that the foundational requirement for the skill originated at the `Team` level, which was initially required at proficiency 60.

This ensures complete auditability of the workforce.
