# Memory System Schema Reference

## `MemoryItem` (Aggregate Root)

| Field | Type | Description |
|---|---|---|
| `memory_id` | `str` | Unique identifier (e.g., `mem_a1b2c3d4`) |
| `organization_id` | `str` | Default `"mycel_global"` |
| `scope` | `MemoryScope` | The hierarchical isolation boundary. |
| `scope_id` | `str` | Identifier matching the scope (e.g. `"developer"`, `"emp_001"`) |
| `memory_type` | `MemoryType` | Semantic classification of the memory. |
| `importance` | `MemoryImportance` | `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` |
| `status` | `MemoryStatus` | `ACTIVE`, `ARCHIVED`, `SUPERSEDED`, `EXPIRED`, `DELETED` |
| `title` | `str` | Concise descriptor (min 3 chars) |
| `content` | `str` | The actual memory insight/summary |
| `summary` | `str` | Truncated fast-lookup summary |
| `tags` | `List[str]` | Keywords for index lookup |
| `source_task_id` | `Optional[str]` | Provenance pointer to originating task |
| `source_work_unit_id` | `Optional[str]` | Provenance pointer to WorkUnit |
| `source_employee_id` | `Optional[str]` | Provenance pointer to Employee |
| `source_team_id` | `Optional[str]` | Provenance pointer to Team |
| `artifact_references` | `List[ArtifactReference]` | Pointers to generated binary artifacts |
| `confidence` | `float` | Reserved for probabilistic logic (defaults to `1.0`) |
| `superseded_by` | `Optional[str]` | Memory ID of the replacement item |
| `created_at` | `datetime` | UTC timestamp |
| `updated_at` | `datetime` | UTC timestamp |
| `expires_at` | `Optional[datetime]` | TTL bound for ephemeral memories |
| `metadata` | `Dict[str, Any]` | Additional internal attributes (sanitized) |

## API Schemas

### `RecordMemoryRequest`
- `scope`: str
- `scope_id`: str
- `memory_type`: str
- `importance`: str
- `title`: str
- `content`: str
- `tags`: List[str]
- `metadata`: Dict[str, Any]

### `QueryMemoryRequest`
- `scope`: str
- `scope_id`: str
- `keywords`: Optional[List[str]]
- `tags`: Optional[List[str]]
- `limit`: int
