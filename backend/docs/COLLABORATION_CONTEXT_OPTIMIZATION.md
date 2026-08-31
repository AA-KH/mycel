# Collaboration Context Optimization

## Purpose
To avoid token explosion, context duplication, and hallucinated instructions, `CollaborationContextBuilder` prunes context to project ONLY the minimal information required by the receiving WorkUnit.

## Projection Rules
1. **Reference-Based Transfer**: Large files or deliverables are passed as `ArtifactReference` pointers (`artifact_id`, `artifact_type`, `format`), NOT raw byte streams.
2. **Input Pruning**: Only fields declared in `required_inputs` of the contract are passed.
3. **No Chain-of-Thought**: Hidden reasoning traces are pruned.
4. **No Unrelated History**: Entire conversation logs or company-wide employee lists are excluded.
