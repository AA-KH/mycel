# Team Registry Contract

The `TeamRegistry` exposes a strict interface for retrieving information about teams.

## Discovery Methods
- `register(team: Team)`: Register a valid team. Rejects duplicates.
- `unregister(team_id: str)`: Remove a team by ID.
- `exists(team_id: str) -> bool`: Check if a team is available.
- `list_teams() -> List[Team]`: Returns all registered teams.
- `list_active() -> List[Team]`: Returns teams with `CompanyStatus.ACTIVE`.

## Retrieval Methods
- `get_team(team_id: str) -> Optional[Team]`: Retrieves the core identity model.
- `get_summary(team_id: str) -> Dict[str, Any]`: Returns a flat dictionary with identity data and statistical counts (useful for UI listings).
- `get_details(team_id: str) -> Dict[str, Any]`: Returns a structured view including pointers to capabilities, members, and pipelines.

## Accessor Methods (Pointers)
The following methods act as pointers. They do not execute the underlying structures.
- `get_positions(team_id: str) -> List[str]`
- `get_members(team_id: str) -> List[str]`
- `get_pipelines(team_id: str) -> List[str]`
- `get_common_skills(team_id: str) -> List[str]`
- `get_common_tools(team_id: str) -> List[str]`

*Note: Accessor methods currently return empty arrays as they are stubs awaiting the integration of dedicated position/member registries.*
