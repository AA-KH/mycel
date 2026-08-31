# Organization Model

The Organization Model defines the structural hierarchy of the company. It serves as the foundation for the Team Operating System (TOS).

## Entities

### Company
- **ID**: `company_id` (e.g. "mycel")
- **Purpose**: The root entity of the organization.
- **Status Options**: DRAFT, ACTIVE, SUSPENDED, ARCHIVED.

### Department
- **ID**: `department_id`
- **Purpose**: A logical grouping of teams within a Company.
- **Constraints**: Must belong to a valid `company_id`.

### Team
- **ID**: `team_id`
- **Purpose**: The core operational unit. Defines *how* a domain works.
- **Constraints**: Must belong to a valid `company_id`. May optionally belong to a `department_id`.

### Position
- **ID**: `position_id`
- **Purpose**: Defines a role within a Team. Outlines requirements and responsibilities.
- **Constraints**: Must belong to a valid `team_id`.

## Status Propagation
When an entity's status changes, it may affect children. Currently, the primary constraint is **Activation Validation**: A child entity (like a Team) cannot be marked `ACTIVE` if its parent (Company) is not `ACTIVE`.
