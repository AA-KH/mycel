# Talent Market Architecture

## Data Flow

```
Workforce (source of truth)
    ↓  [TalentSnapshotBuilder]
TalentCapabilitySnapshot (projection)
    ↓  stored in TalentRegistry
TalentSearchRequest
    ↓  [TalentCandidateFilter]   ← hard gates applied FIRST
Eligible Snapshots
    ↓  [TalentCandidateMatcher]
CandidateMatchBreakdowns
    ↓  [TalentCandidateRanker]
CandidateReference list (top-K, paginated)
    ↓  handed to Hiring System
Hiring System (revalidates + selects)
```

## Projection Strategy
`TalentCapabilitySnapshot` is a derived, eventually consistent view:
- Built from `Employee.skills`, `Employee.permissions`, upskill capabilities (injected), workload (injected)
- Stored in `TalentRegistry` (in-memory; MongoDB-ready)
- Invalidated on EMPLOYEE_UPDATED / SKILL_UPDATED / TOOL_PERMISSION_CHANGED / UPSKILL_ACTIVATED / UPSKILL_REVOKED events
- `snapshot_version` tracks freshness; `is_stale` flag set on invalidation

## Snapshot Lifecycle
```
Employee created / updated
    → TalentSnapshotBuilder.build(employee)
    → TalentRegistry.register(snapshot)
    
Employee skill changes
    → TalentRegistry.invalidate(employee_id)
    → snapshot.is_stale = True
    → Next build_snapshot() increments version

Hiring selects candidate
    → MUST revalidate against authoritative Employee state
    → Never trust stale snapshot for final hire decision
```

## Key Boundaries
| System | Owns | Talent Market... |
|---|---|---|
| Employee Registry | Employee identity + status | Reads (projects) |
| Skill Registry | Skill definitions | Reads proficiency from Employee |
| Tool Registry | Tool catalogue | Reads authorized_tools via permissions |
| Upskill System | Active upskill capabilities | Consumes injected capability IDs |
| Evaluation System | Performance measurement | Reads PerformanceSummary from Employee |
| Memory System | Learned context | Does NOT search |
| Hiring System | Selection decision | Returns CandidateReference to it |
