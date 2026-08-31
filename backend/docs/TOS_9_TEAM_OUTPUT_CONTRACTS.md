# Phase TOS 9: Team Output Contracts

## Overview
Phase TOS 9 establishes a first-class Output Contract System that defines exactly what a Team, Pipeline, or Stage is expected to produce. It clearly separates:
- **Task Request**: Natural language request from the user.
- **Expected Output**: Defined by the `OutputContract` (WHAT must exist).
- **Actual Output**: The generated data, specifically referencing an `ArtifactReference`.
- **Output Quality**: Defined by `QualityGate` (Is what exists good enough?).

The Output Contract ensures a deterministic expectation of deliverables without muddying the waters with Cloudinary upload logic or Quality evaluating logic.

## Output vs Artifact System
`OutputContract` defines WHAT deliverable is expected (e.g. `artifact_required=True`, `output_type=VIDEO`, `formats=["mp4"]`). The `ArtifactSystem` handles HOW it is stored and referenced. An output contract validates an `ArtifactReference` object representing the deliverable, ensuring no binary files are stored in the contract itself.
