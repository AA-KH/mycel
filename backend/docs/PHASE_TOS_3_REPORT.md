# Phase TOS 3 Report

## STATUS
**COMPLETE.** The Team Common Tools System has been successfully integrated into the Mycel Team Operating System.

## TOOL & TEAM TOOL MODEL
Preserved the existing global `ToolDefinition` (in `tools/models.py`) and introduced `TeamToolAssignment` (in `tools/team/models.py`) to manage team-level access pools without duplicating execution definitions.

## TEAM TOOL ASSIGNMENTS
Teams can now reference global tools. The assignment stores `importance` (CORE, SUPPORTING, OPTIONAL), a `required` boolean flag, and an `access_mode` (READ, WRITE, EXECUTE, FULL). The system validates that global tools actually exist and are enabled before allowing assignment.

## TOOL REGISTRIES
- `ToolRegistry` (Global): Continues to act as the source of truth for execution definitions.
- `TeamToolRegistry` (Domain): Introduced to resolve the specific list of tools available to a Team, joining the assignment data with the global definitions.

## DATABASE COLLECTIONS
- `team_tools` (Domain: `TeamToolAssignment`)

## INDEXES
- Planned/Assumed compound index on `team_id` and `tool_id` to ensure unique assignments and rapid querying.

## API ENDPOINTS
- `GET /api/v1/tools` (Global)
- `GET /api/v1/tools/{tool_id}` (Global)
- `GET /api/v1/teams/{team_id}/tools`
- `POST /api/v1/teams/{team_id}/tools`
- `PATCH /api/v1/teams/{team_id}/tools/{tool_id}`
- `DELETE /api/v1/teams/{team_id}/tools/{tool_id}` (Soft deletes via INACTIVE status)

## VALIDATION
- Rejecting missing teams via `TeamRegistry`.
- Rejecting missing/disabled tools via global `ToolRegistry`.
- Rejecting duplicate assignments via MongoDB/Service-level lookup.

## SEED RESULTS
Developed `backend/tools/team/seed.py` which idempotently registers the baseline tools (e.g., `web.search`, `filesystem.write`) into the global registry, and assigns the Engineering catalog to the `team-backend` team (created in TOS 1). 
*Note: Seed explicitly only uses tools that have concrete mock implementations.*

## TEST RESULTS
`tests/tools/test_team_tools.py` successfully validates assignment uniqueness, rejection of invalid tools, and rejection of globally disabled tools.

## FILES CREATED
- `tools/team/models.py`
- `tools/team/schemas.py`
- `tools/team/repository.py`
- `tools/team/registry.py`
- `tools/team/service.py`
- `tools/team/catalogue.py`
- `tools/team/seed.py`
- `tests/tools/test_team_tools.py`
- `api/dependencies/tools.py`
- `api/v1/routes/tools.py`
- `docs/TOS_3_TEAM_COMMON_TOOLS.md`
- `docs/TEAM_TOOL_MODEL.md`
- `docs/TOOL_ACCESS_MODEL.md`
- `docs/PHASE_TOS_3_REPORT.md`

## FILES MODIFIED
- `api/v1/router.py`

## TECHNICAL DEBT
- MongoDB indexes for `team_tools` are assumed in code but rely on the broader infrastructure initialization to create actual compound uniqueness constraints in production.

## NEXT PHASE
TOS 4 — Team Knowledge System
