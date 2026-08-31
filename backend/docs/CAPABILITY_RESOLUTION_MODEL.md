# Capability Resolution Model

## How Effective Capability is Calculated

The `CapabilityResolver` calculates the final operational floor for any structural entity by traversing from the highest abstract tier (Team) down to the most specific tier (Specialization).

### Example Resolution

#### 1. Team Contribution (Developer Team)
- Skill: `programming` (Proficiency: 60, Status: REQUIRED)
- Tool: `git` (Status: REQUIRED)
- Tool: `production_db` (Status: DENIED)

#### 2. Position Contribution (Backend Engineer)
- Skill: `programming` (Proficiency: 70) -> *Overrides Team proficiency.*
- Skill: `python` (Status: OPTIONAL) -> *Added.*
- Tool: `docker` (Status: REQUIRED) -> *Added.*
- Tool: `production_db` (Status: REQUIRED) -> *IGNORED. Team DENY overrides.*

#### 3. Member Specialization (Kabir)
- Skill: `programming` (Proficiency: 85) -> *Overrides Position proficiency.*
- Skill: `python` (Status: REQUIRED) -> *Upgrades OPTIONAL to REQUIRED.*
- Tool: `kubernetes` (Status: REQUIRED) -> *Added.*

#### Resulting Effective Capability:
- `programming`: 85 (REQUIRED)
- `python`: None (REQUIRED)
- `git`: (REQUIRED)
- `docker`: (REQUIRED)
- `kubernetes`: (REQUIRED)
- `production_db`: (DENIED)

## Resolution Result
The final object passed to the Agent Runtime is the `CapabilityResolutionResult`, containing the flattened array of `ResolvedCapability` objects, explicit tracking of all `conflicts`, any calculated `gaps`, and full `provenance` metadata.
