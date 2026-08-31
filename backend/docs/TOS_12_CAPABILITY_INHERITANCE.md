# TOS 12: Capability Inheritance

The Capability Inheritance system dynamically resolves what an Agent can do by analyzing its structural hierarchy. Instead of duplicating definitions, the system computes an `EffectiveCapabilitySnapshot` at runtime.

## The Inheritance Chain

```text
TEAM COMMON (The baseline for all team members)
    ↓
POSITION (Role-specific requirements)
    ↓
BASELINE MEMBER (Standard expected worker)
    ↓
ACTUAL MEMBER (Individual specialization)
```

## Core Principles

1. **Resolution over Duplication:** Capabilities are declared exactly once at their appropriate abstraction level and resolved dynamically.
2. **Determinism:** Given the same structural inputs, the resolver will always compute the same capability set. It relies on strict logic, never LLM inference.
3. **Least Privilege:** A member never inherently receives capabilities from adjacent teams or peers.
4. **Deny Overrides Allow:** For security reasons, if a higher level (like the Team) explicitly denies a capability (e.g., `production_database`), no child entity can override it.
5. **Required Upgrades:** If a parent layer makes a capability `REQUIRED`, a child layer cannot downgrade it to `OPTIONAL`.

## Capability Types

Capabilities are diverse and inherit differently:
- **SKILLS**: Combine proficiency scores. A child's explicit proficiency overrides the parent's.
- **TOOLS**: Follow strict allow/deny access models.
- **KNOWLEDGE**: Merges RAG collections.
- **REASONING**: Stacks cognitive processing rules.
- **PIPELINES/STAGES/OUTPUTS/QUALITY**: Propagates execution responsibilities.

## Caching and Snapshots

To prevent performance bottlenecks and ensure historical accuracy (explainability), resolved capabilities are stored as `CapabilitySnapshots`. If a task runs today, the runtime uses today's snapshot. If Team requirements change tomorrow, past execution records remain valid because they reference the specific snapshot hash valid at that time.
