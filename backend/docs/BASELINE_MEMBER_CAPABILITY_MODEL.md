# Baseline Member Capability Model

The Capability Model for a Baseline Member represents the exact calculated summation of two strict architectural layers: The **Team**, and the **Position**.

## The Resolution Formula

```text
  Team Common Capabilities (Mandatory for all team members)
+ Position Requirements (Specific to the role)
=========================================================
= Baseline Member Capability (The operational floor)
```

## How Capabilities Resolve

### 1. Skills
- **Team Contribution:** If the Developer team requires `programming` and `debugging`, the Baseline Member inherits these with a default baseline proficiency (e.g., level 70).
- **Position Contribution:** If the Backend Engineer position requires `python`, it is added to the profile.
- **Conflict Resolution:** A Position cannot weaken a Team skill. If a position tries to omit or make a Team skill optional, the `BaselineMemberValidator` immediately throws a `DomainError`.

### 2. Tools
- **Team Contribution:** The Developer team provides `git`.
- **Position Contribution:** The Backend Engineer position adds `terminal` and `github`.
- **Final Loadout:** `[git, terminal, github]`. The baseline member explicitly does *not* receive high-privilege tools (e.g. `aws_admin`) unless strictly defined.

### 3. Knowledge & Reasoning
- The baseline member concatenates the `knowledge_space` RAG collections from both the Team and the Position.
- The `reasoning_profile` (e.g., `engineering_reasoning`) cascades down to ensure the baseline thinker uses the appropriate cognitive framework.
