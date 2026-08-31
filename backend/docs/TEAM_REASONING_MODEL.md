# Team Reasoning Model

## Core Entities
1. **TeamReasoningProfile**: A versioned aggregate root defining the high-level methodology for a single team. It contains declarative `principles` (e.g. `["understand_before_modify", "test_before_completion"]`) and structured `policies`.
2. **TeamReasoningStrategyAssignment**: Maps a Team's profile to a statically defined, global `ReasoningStrategy` (e.g., `code_test`, `research_verify`) loaded by the `ReasoningEngine`.

## Reasoning Policies
Policies are structured rules that govern execution constraints.
- `EvidencePolicy`: Handles source preferences and citation requirements.
- `VerificationPolicy`: Defines when outputs require explicit verification steps.
- `UncertaintyPolicy`: Defines how the agent should act when lacking information (e.g. `admit_unknowns = True`).
- `QualityPolicy`: Focuses on domain-specific correctness.
- `OutputPolicy`: Instructs the structure of the final output (e.g. `include_confidence_notes = True`).

## Lifecycle
A Team can have multiple Profiles historically, but only ONE `active` profile at any given time, enforced by the `TeamReasoningRegistry`.
