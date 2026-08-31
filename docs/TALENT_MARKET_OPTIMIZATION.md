# Talent Market Optimization Guide

## Core Principle: Filter First, Then Rank

```
DATABASE FILTER (team, status, availability)
    ↓ small candidate set
CAPABILITY VALIDATION (skills, tools, capabilities)
    ↓ eligible candidates only
MATCH SCORE COMPUTATION
    ↓ scored list
TOP-K (return bounded result)
```

Never load all employees and compute everything in Python first.

## Indexing Strategy
For MongoDB-backed production deployments, index on:
- `employee_id`
- `team_id`
- `position_id`
- `availability`
- `is_stale`
- `skills.*` (multikey index on skill IDs)
- `authorized_tools` (multikey index)
- `capabilities` (multikey index)

## LLM Minimization
- Structured `TalentSearchRequest` → zero LLM calls
- LLM only permitted for natural-language requirement extraction (future Phase)
- LLM must never directly select a candidate
- LLM output must always be converted to structured `TalentSearchRequest` first

## Snapshot Invalidation Strategy
Events that trigger `TalentRegistry.invalidate()`:
- `EMPLOYEE_UPDATED`
- `SKILL_PROFICIENCY_CHANGED`
- `TOOL_PERMISSION_CHANGED`
- `UPSKILL_ACTIVATED`
- `UPSKILL_REVOKED`
- `TEAM_MEMBERSHIP_CHANGED`
- `POSITION_CHANGED`

## Pagination
- All eligible candidates are ranked before slicing
- Offset + limit applied after ranking (correct cursor semantics)
- `has_more` field indicates whether further pages exist
- Hard ceiling: `limit <= 100` per request

## NOT_EVALUATED Performance
Dimensions with no data are excluded from the score denominator.
This ensures that a candidate with missing workload information is never artificially scored as 0 — they simply have that dimension excluded from weighting.
