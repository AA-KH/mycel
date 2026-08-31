# TOS 1: Organization & Team Identity System

## Objective
Establish the primary organizational structure entities—Company, Department, Team, and Position—as first-class domain models, with clear hierarchical boundaries and lifecycle rules.

## Domains Refactored
The monolithic `organization` module has been split into:
- `organization/company/`
- `organization/departments/`
- `organization/teams/`
- `organization/positions/`

## Key Architectural Principles Enforced
1. **Hierarchical Dependencies**: 
   - A Department must belong to a Company.
   - A Team must belong to a Company, and optionally to a Department.
   - A Position must belong to a Team.
2. **Lifecycle Rules**:
   - An entity cannot transition to `ACTIVE` unless its parent is `ACTIVE`.
   - Entities are soft-deleted via the `ARCHIVED` status. Mutating an `ARCHIVED` entity is prohibited.
3. **Identity Resolution**:
   - `OrganizationRegistry` provides safe lookups.
   - `TeamRegistry` specifically resolves Team entities.

## Next Steps
- Expose the newly created API routes to frontend if applicable.
- Proceed to Employee lifecycle mapping (TOS 2).
