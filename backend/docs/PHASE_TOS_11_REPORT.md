# Phase TOS 11 Report: Baseline Team Members

## Implementation Summary
Phase TOS 11 formally introduced the **Baseline Team Member** layer to the Mycel Team Operating System. This layer solves the conceptual gap between abstract, un-executable `Positions` and highly specialized `Employees`. A Baseline Member defines the minimum operational identity required to fulfill a specific team seat, enabling deterministic capability matching for the future Smart Hiring engine without directly spinning up Agents.

## Domain Architecture
The implementation added a cohesive `workforce/baseline_members/` package:
- **Model:** Defined the `BaselineMember` domain entity ensuring stable identities (e.g. `developer_backend_baseline`), explicit reference fields, and strict lifecycle status tracking.
- **Registries:** Built `BaselineMemberRegistry` and `BaselineMemberRepository` capable of retrieving baselines by team, position, skills, tools, and outputs.
- **Validation:** Implemented `BaselineMemberValidator` to rigorously ensure Baseline-Team-Position compatibility. It asserts that team boundary assumptions are safe and prevents baselines from dropping mandatory Team Common Requirements.
- **Resolution Engine:** `BaselineCapabilityResolver` was built to procedurally resolve and combine parent Team requirements with Position specifications into a final Effective Baseline profile.
- **Catalogue Seeding:** Added `BaselineMemberCatalogue` loader to dynamically discover and seed all definitions generated in the filesystem.

## Baseline Member Catalogue Generation
Generated 28 deterministic Baseline Member models corresponding to all valid Positions across the 7 organization teams (Developer, Research, Creative, Legal, Marketing, Finance, Operations).
These definitions reside physically grouped with their teams at `teams/<team_id>/team_members/baseline/<position_id>.py` following the standard decentralized architecture.

## Existing Member Integration
Upgraded existing Employee profiles (`emp_kabir_sharma`, `emp_aarav_mehta`, `emp_riya_sharma`) bridging them to the newly established baselines.
- Kabir (`emp_kabir_sharma`) → `developer_backend_baseline`
- Aarav (`emp_aarav_mehta`) → `research_researcher_baseline`
- Riya (`emp_riya_sharma`) → `creative_video_producer_baseline`
Additionally, aligned all legacy arbitrary `team_id` designations (e.g. `team_backend`) to match the canonical locked structural IDs (`developer`).

## Testing & Validation
Implemented 10 strict validation test scenarios in `tests/workforce/test_baseline_members.py`:
- Verified Baseline Capability Resolution mathematics (`Team + Position`).
- Verified 8 Negative Exception states (Cross-team references, Unknown Skills, Unknown Tools, Unknown Positions, Weakening Mandatory Constraints).
- Verified pure structural compliance (No LLM, No Agent, No Employee creation).
- **Test execution passed flawlessly with 0 failures.**

## Files Created/Modified
- `workforce/baseline_members/models.py` (Created)
- `workforce/baseline_members/repository.py` (Created)
- `workforce/baseline_members/registry.py` (Created)
- `workforce/baseline_members/validator.py` (Created)
- `workforce/baseline_members/resolver.py` (Created)
- `workforce/baseline_members/catalogue.py` (Created)
- `workforce/employees/models.py` (Modified - Added `baseline_member_id`)
- `teams/<team>/team_members/baseline/*.py` (Created 28 baseline catalogue files)
- `teams/*/team_members/emp_*/profile.py` (Modified 3 employee profiles)
- `tests/workforce/test_baseline_members.py` (Created)

## Future Smart Hiring Integration
The boundary is structurally locked exactly before Individual Specialization. The hiring engine built in future phases will now simply compare the global catalogue of `Employee` objects against the newly established `BaselineMember` profiles using delta calculations to score hiring candidates.

**PHASE TOS 11 IS COMPLETE.**
