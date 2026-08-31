# Position Capability Profile

The `EffectivePositionCapabilityProfile` is the resolved union of:
1. Team Common Capabilities (Skills, Tools, Knowledge, Reasoning)
2. Position-specific Capabilities

## Resolving Rules
- **Inheritance**: A Position inherits all mandatory Team capabilities.
- **Tightening**: A Position can specify higher proficiency thresholds for inherited Team skills.
- **No Weakening**: A Position CANNOT downgrade a mandatory Team skill to optional. If a Team requires `software_development`, the Position must as well.

The `PositionCapabilityResolver` handles this merging logic safely.
